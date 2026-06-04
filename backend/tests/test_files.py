import io
import pytest

def test_file_upload_and_list(client, test_user):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    
    file_content = b"Mock GnuCash file content"
    files = {"file": ("test_data.gnucash", io.BytesIO(file_content), "application/octet-stream")}
    
    # Upload
    res_upload = client.post("/api/files/upload", headers=headers, files=files)
    assert res_upload.status_code == 201
    assert res_upload.json()["filename"] == "test_data.gnucash"
    
    # List
    res_list = client.get("/api/files/", headers=headers)
    assert res_list.status_code == 200
    files_list = res_list.json()
    assert len(files_list) > 0
    assert any(f["filename"] == "test_data.gnucash" for f in files_list)

def test_file_upload_invalid_extension(client, test_user):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    files = {"file": ("malicious.exe", io.BytesIO(b"bad"), "application/octet-stream")}
    
    res = client.post("/api/files/upload", headers=headers, files=files)
    assert res.status_code == 400
    assert "not allowed" in res.json()["detail"]

def test_file_download(client, test_user):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    
    # First upload
    file_content = b"Data to download"
    files = {"file": ("download.csv", io.BytesIO(file_content), "text/csv")}
    client.post("/api/files/upload", headers=headers, files=files)
    
    # Then download
    res = client.get("/api/files/download/download.csv", headers=headers)
    assert res.status_code == 200
    assert res.content == file_content

def test_file_delete(client, test_user):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    
    # Upload
    files = {"file": ("delete_me.qif", io.BytesIO(b"abc"), "text/plain")}
    client.post("/api/files/upload", headers=headers, files=files)
    
    # Delete
    res = client.delete("/api/files/delete_me.qif", headers=headers)
    assert res.status_code == 200
    
    # Ensure gone
    res_list = client.get("/api/files/", headers=headers)
    assert not any(f["filename"] == "delete_me.qif" for f in res_list.json())
