
from pathlib import Path

def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_document(client):
    file_content = b"# Atlas\nThis is a markdown file."

    response = client.post(
        "/documents",
        files={
            "file": ("atlas.md", file_content, "text/markdown")
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "atlas.md"
    assert data["status"] == "uploaded"
    assert data["content_type"] == "text/markdown"

    # verify file exists
    path = Path("storage") / f"{data['id']}.md"
    assert path.exists()

def test_list_documents(client):
    client.post(
        "/documents",
        files={
            "file": (
                "notes.md",
                b"hello",
                "text/markdown",
            )
        },
    )

    response = client.get("/documents")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "notes.md"

def test_get_documents_by_id(client):
    upload = client.post(
            "/documents",
            files={
                "file": (
                    "notes.md",
                    b"hello",
                    "text/markdown",
                )
            },
        )
    doc = upload.json()
    file_path = Path("storage") / f"{doc['id']}.md"
    
    assert file_path.exists()

    response = client.get(f"/documents/{doc['id']}")

    doc_returned = response.json()
    assert doc['id']==doc_returned['id']




    


def test_delete_document(client):
    upload = client.post(
        "/documents",
        files={
            "file": (
                "delete_me.md",
                b"temporary",
                "text/markdown",
            )
        },
    )

    document = upload.json()

    file_path = Path("storage") / f"{document['id']}.md"

    assert file_path.exists()

    response = client.delete(
        f"/documents/{document['id']}"
    )

    assert response.status_code == 204

    assert not file_path.exists()

    get_response = client.get("/documents")

    ids = [doc["id"] for doc in get_response.json()]

    assert document["id"] not in ids


