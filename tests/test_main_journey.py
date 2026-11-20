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
    sys.modules.pop("app", None)
    app = importlib.import_module("app")
    from fastapi.testclient import TestClient
    with TestClient(app.app) as client:
        assert client.get("/").status_code == 200
        assert client.post("/api/login", json={"username":"lead","password":"wrong"}).status_code == 401
        def auth(role):
            response = client.post("/api/login", json={"username":role,"password":"testing-only-password"})
            assert response.status_code == 200, response.text
            return {"Authorization":"Bearer "+response.json()["token"]}
        lead, reviewer, newcomer = auth("lead"), auth("reviewer"), auth("newmember")
        assert client.get("/api/sources",headers=lead).json() == []
        assert client.post("/api/chat",headers=lead,json={"question":"What decisions?"}).json()["insufficient_evidence"]
        assert client.post("/api/sources",headers=lead,files={"file":("virus.exe",b"bad")}).status_code == 400
        doc = b"2026-11-20 Decided to use Supabase because reliable storage is required.\nTODO: Assigned to lead to implement search indexing.\nRisk: API outage may block semantic search.\n"
        upload=client.post("/api/sources",headers=lead,files={"file":("notes.txt",doc,"text/plain")},data={"visibility":"all"})
        assert upload.status_code == 200, upload.text
        sid=upload.json()["id"]
        assert len(client.get("/api/sources",headers=newcomer).json()) == 1
        assert client.get("/api/sources/"+str(sid),headers=newcomer).status_code == 200
        decisions=client.get("/api/decisions",headers=lead)
        assert decisions.status_code==200 and decisions.json()["count"]>=1
        result=client.post("/api/chat",headers=lead,json={"question":"What was decided about Supabase?","engine":"search"})
        assert result.status_code==200 and result.json()["citations"]
        restricted=client.post("/api/sources",headers=lead,files={"file":("secret.txt",b"Decision: use internal process because secret.","text/plain")},data={"visibility":"restricted"})
        assert restricted.status_code==200
        assert len(client.get("/api/sources",headers=newcomer).json())==1
        create=client.post("/api/handovers",headers=lead,json={"recipient_role":"incoming"})
        assert create.status_code==200,create.text
        hid=create.json()["id"]
        assert client.get("/api/handovers/"+str(hid),headers=newcomer).status_code==403
        details=client.get("/api/handovers/"+str(hid),headers=reviewer).json()
        assert details["claims"]
        assert client.post("/api/handovers/"+str(hid)+"/approve",headers=reviewer).status_code==400
        for claim in details["claims"]:
            response=client.post("/api/handovers/"+str(hid)+"/review",headers=reviewer,json={"claim_id":claim["claim_id"],"verdict":"accept"})
            assert response.status_code==200,response.text
        assert client.post("/api/handovers/"+str(hid)+"/approve",headers=reviewer).status_code==200
        assert client.post("/api/handovers/"+str(hid)+"/approve",headers=reviewer).status_code==409
        assert client.get("/api/handovers/"+str(hid),headers=newcomer).status_code==200
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
