import requests
import subprocess


def _get_oidc_token():
    p = subprocess.run(
        [
            r"C:\projects\token-exchange\dist\tx_windows_amd64.exe",
            "cognito",
            "--output",
            "id",
        ],
        capture_output=True,
    )
    if p.returncode != 0:
        raise Exception("failed to refresh token")
    return p.stdout.decode()


def main():
    token = _get_oidc_token()
    headers = {"Authorization": f"Bearer {token}"}

    # submit
    r = requests.post(
        "https://api-workflow-broker.noxide.xyz/dev/submit", headers=headers
    )
    out = r.json()
    print(f"{r.status_code}: {out}")

    # upload input_test.json
    file_to_upload = "input_test.json"
    with open(file_to_upload, "rb") as f:
        files = {"file": (file_to_upload, f)}
        r = requests.post(out["url"], data=out["fields"], files=files)
    print(f"{r.status_code}: {r.content.decode()}")


if __name__ == "__main__":
    main()
