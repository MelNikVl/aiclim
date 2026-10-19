# TasteDistrict working instructions

- The designated development and runtime server is `nik@192.168.0.15`, checkout `/home/nik/tastedistrict`. Prefer this server for builds and runtime verification. Do not leave a workstation localhost process as the primary demo.
- The LAN demo is `http://192.168.0.15:8000`, served by the dedicated Docker container `tastedistrict`. Keep the explicit LAN binding and restart policy; see `docs/DEPLOY.md` for operations and verified runtime restrictions.
- This server also hosts unrelated projects. Operate only on the TasteDistrict checkout, images and container. Never restart or prune the Docker host, copy another project's code/data, or modify its services.
- Keep credentials in the private server `.env`, never in source, browser code, prompts, logs or committed response fixtures. Preserve the existing environment file on updates without printing it.
- Use clearly labeled synthetic Demo data until the event credential and real API behavior have been verified. Do not claim real city coverage, a completed LLM comparison or submission readiness from synthetic tests.
- User approval for LAN deployment and the existing draft PR is recorded in this chat. External publication, new accounts, paid resources and repository visibility changes remain separate actions requiring the user's authorization.
- Record the deployed application revision, image and observed checks in `docs/VERIFICATION.md`. A documentation-only checkout update does not require rebuilding an unchanged application image.
