import os
import sys
import importlib

def test_main_journey(tmp_path, monkeypatch):
    monkeypatch.setenv("HANDOVERIQ_DB", str(tmp_path / "handover.sqlite3"))
    monkeypatch.setenv("AUTH_SECRET", "testing-only-distinct-auth-secret")
    monkeypatch.setenv("DEMO_PASSWORD", "testing-only-password")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_URL", raising=False)
    monkeypatch.setenv("JUDGE_DEMO_ENABLED","1")
    sys.modules.pop("app", None)
    app = importlib.import_module("app")
    from fastapi.testclient import TestClient
    with TestClient(app.app) as client:
        assert client.get("/").status_code == 200
        assert client.get("/api/health").json()["database"] == "sqlite"
        assert client.get("/api/judge/config").json()["enabled"] is True
        assert client.post("/api/chat",json={"question":"What happened?","source_id":1}).status_code==401
        assert client.get("/api/continuity/score").status_code == 401
        assert client.post("/api/login", json={"username":"lead","password":"wrong"}).status_code == 401
        def auth(role):
            response = client.post("/api/login", json={"username":role,"password":"testing-only-password"})
            assert response.status_code == 200, response.text
            return {"Authorization":"Bearer "+response.json()["token"]}
        lead, reviewer, newcomer = auth("lead"), auth("reviewer"), auth("newmember")
        assert client.get("/api/sources",headers=lead).json() == []
        assert client.post("/api/chat",headers=lead,json={"question":"What decisions?","source_id":1}).status_code==404
        assert client.post("/api/chat",headers=lead,json={"question":"What decisions?"}).status_code==400
        assert client.post("/api/sources",headers=lead,files={"file":("virus.exe",b"bad")}).status_code == 400
        doc = b"2026-11-20 Decided to use Supabase because reliable storage is required.\nTODO: Assigned to lead to implement search indexing.\nRisk: API outage may block semantic search.\n"
        upload=client.post("/api/sources",headers=lead,files={"file":("notes.txt",doc,"text/plain")},data={"visibility":"all"})
        assert upload.status_code == 200, upload.text
        sid=upload.json()["id"]
        repeated=client.post("/api/sources",headers=lead,files={"file":("notes.txt",doc,"text/plain")},data={"visibility":"all"})
        assert repeated.status_code==200 and repeated.json()["duplicate"] and repeated.json()["id"]==sid
        assert len(client.get("/api/sources",headers=newcomer).json()) == 1
        assert client.get("/api/sources/"+str(sid),headers=newcomer).status_code == 200
        score=client.get("/api/continuity/score",headers=lead)
        assert score.status_code==200 and 0 <= score.json()["score"] <= 100
        decisions=client.get("/api/decisions",headers=lead)
        assert decisions.status_code==200 and decisions.json()["count"]>=1
        result=client.post("/api/chat",headers=lead,json={"question":"What was decided about Supabase?","engine":"search","source_id":sid})
        assert result.status_code==200 and result.json()["citations"]
        restricted=client.post("/api/sources",headers=lead,files={"file":("secret.txt",b"Decision: use internal process because secret.","text/plain")},data={"visibility":"restricted"})
        assert restricted.status_code==200
        # A question scoped to the first file cannot cite another uploaded file.
        second=client.post("/api/sources",headers=lead,files={"file":("other.txt",b"Quantum banana rockets were discussed and selected.", "text/plain")},data={"visibility":"all"})
        assert second.status_code==200
        r=client.post("/api/chat",headers=lead,json={"question":"What about quantum banana rockets?","engine":"search","source_id":sid})
        assert r.status_code==200 and r.json()["insufficient_evidence"]
        r=client.post("/api/chat",headers=lead,json={"question":"What about quantum banana rockets?","engine":"search","source_id":second.json()["id"]})
        assert r.status_code==200 and r.json()["citations"]
        assert all(c["source_id"]==second.json()["id"] for c in r.json()["citations"])
        assert client.post("/api/chat",headers=newcomer,json={"question":"What secret?","source_id":restricted.json()["id"]}).status_code==404
        assert len(client.get("/api/sources",headers=newcomer).json())==2
        create=client.post("/api/handovers",headers=lead,json={"recipient_role":"incoming"})
        assert create.status_code==200,create.text
        hid=create.json()["id"]
        assert client.get("/api/handovers/"+str(hid),headers=newcomer).status_code==403
        details=client.get("/api/handovers/"+str(hid),headers=reviewer).json()
        assert details["claims"]
        assert client.post("/api/handovers/"+str(hid)+"/approve",headers=reviewer).status_code==400
        for claim in details["claims"]:
            verdict="reject" if claim["claim_id"]==0 else "accept"
            response=client.post("/api/handovers/"+str(hid)+"/review",headers=reviewer,json={"claim_id":claim["claim_id"],"verdict":verdict})
            assert response.status_code==200,response.text
        assert client.post("/api/handovers/"+str(hid)+"/approve",headers=reviewer).status_code==200
        assert client.post("/api/handovers/"+str(hid)+"/approve",headers=reviewer).status_code==409
        assert client.get("/api/handovers/"+str(hid),headers=newcomer).status_code==200
        visible=client.get("/api/handovers/"+str(hid),headers=newcomer).json()
        assert len(visible["claims"])==len(details["claims"])-1
        assert client.post("/api/handovers/"+str(hid)+"/acknowledge",headers=newcomer).status_code==400
        for day in range(1,8):
            r=client.post("/api/handovers/"+str(hid)+"/progress",headers=newcomer,json={"day":day,"completed":True})
            assert r.status_code==200,r.text
        assert client.get("/api/handovers/"+str(hid),headers=newcomer).json()["progress_percent"]==100
        assert client.post("/api/handovers/"+str(hid)+"/acknowledge",headers=newcomer).status_code==200
        assert client.post("/api/handovers/"+str(hid)+"/acknowledge",headers=newcomer).status_code==200
        assert client.get("/api/handovers/"+str(hid)+"/export",headers=newcomer).status_code==200
        assert client.post("/api/handovers/"+str(hid)+"/progress",headers=newcomer,json={"day":1,"completed":False}).status_code==200
        assert client.get("/api/handovers/"+str(hid),headers=newcomer).json()["progress_percent"]==86
        assert client.get("/api/sources/"+str(sid),headers=newcomer).status_code==200
        # Public judge accounts are isolated from the private source workspace.
        demo=client.post("/api/judge/login",json={"username":"lead"})
        assert demo.status_code==200,demo.text
        judge={"Authorization":"Bearer "+demo.json()["token"]}
        assert client.get("/api/me",headers=judge).json()["demo"] is True
        assert client.get("/api/sources",headers=judge).json()==[]
        sample=client.post("/api/sources",headers=judge,files={"file":("judge.txt",b"Decision: use demo workspace because judge data must stay separate.", "text/plain")},data={"visibility":"all"})
        assert sample.status_code==200,sample.text
        assert client.get("/api/sources",headers=judge).json()[0]["filename"]=="judge.txt"
        assert any(x["filename"]=="notes.txt" for x in client.get("/api/sources",headers=lead).json())
