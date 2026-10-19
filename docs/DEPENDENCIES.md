# Dependency license inventory

Inspected **2026-10-19** using `importlib.metadata` in the local Python 3.11 Windows `.venv`, including each installed distribution's license metadata and packaged license-file presence. Direct dependency versions come from `pyproject.toml`; package records link to the publisher's version-specific PyPI metadata.

This inventory covers installed distributions, not every component bundled in the Python interpreter or a container base image. Docker build and startup passed in [GitHub Actions](https://github.com/MelNikVl/aiclim/actions/runs/39207700404); the local Docker daemon remained unavailable. Runtime/test versions are pinned in `constraints.txt`, but platform-specific dependencies and base-image components may differ. Regenerate the inventory from the final deployment environment before distributing an image.

| Distribution | Installed version | Declared license | Role |
| --- | --- | --- | --- |
| [fastapi](https://pypi.org/pypi/fastapi/0.135.1/json) | 0.135.1 | MIT | Direct runtime |
| [httpx](https://pypi.org/pypi/httpx/0.28.1/json) | 0.28.1 | BSD-3-Clause | Direct runtime |
| [pydantic-settings](https://pypi.org/pypi/pydantic-settings/2.13.1/json) | 2.13.1 | MIT | Direct runtime |
| [uvicorn](https://pypi.org/pypi/uvicorn/0.41.0/json) | 0.41.0 | BSD-3-Clause | Direct runtime |
| [pytest](https://pypi.org/pypi/pytest/9.0.2/json) | 9.0.2 | MIT | Direct test |
| [pytest-asyncio](https://pypi.org/pypi/pytest-asyncio/1.3.0/json) | 1.3.0 | Apache-2.0 | Direct test |
| [annotated-doc](https://pypi.org/pypi/annotated-doc/0.0.5/json) | 0.0.5 | MIT | Transitive |
| [annotated-types](https://pypi.org/pypi/annotated-types/0.8.0/json) | 0.8.0 | MIT | Transitive |
| [anyio](https://pypi.org/pypi/anyio/4.15.1/json) | 4.15.1 | MIT | Transitive |
| [certifi](https://pypi.org/pypi/certifi/2026.10.18/json) | 2026.10.18 | MPL-2.0 | Transitive; weak copyleft |
| [click](https://pypi.org/pypi/click/8.5.0/json) | 8.5.0 | BSD-3-Clause | Transitive |
| [colorama](https://pypi.org/pypi/colorama/0.4.6/json) | 0.4.6 | BSD-3-Clause | Windows transitive; license text inspected |
| [h11](https://pypi.org/pypi/h11/0.16.0/json) | 0.16.0 | MIT | Transitive |
| [httpcore](https://pypi.org/pypi/httpcore/1.0.9/json) | 1.0.9 | BSD-3-Clause | Transitive |
| [idna](https://pypi.org/pypi/idna/3.20/json) | 3.20 | BSD-3-Clause | Transitive |
| [iniconfig](https://pypi.org/pypi/iniconfig/2.3.1/json) | 2.3.1 | MIT | Test transitive |
| [packaging](https://pypi.org/pypi/packaging/26.3/json) | 26.3 | Apache-2.0 OR BSD-2-Clause | Test transitive |
| [pluggy](https://pypi.org/pypi/pluggy/1.7.0/json) | 1.7.0 | MIT | Test transitive |
| [pydantic](https://pypi.org/pypi/pydantic/2.14.1/json) | 2.14.1 | MIT | Transitive |
| [pydantic_core](https://pypi.org/pypi/pydantic-core/2.50.1/json) | 2.50.1 | MIT | Transitive |
| [Pygments](https://pypi.org/pypi/Pygments/2.21.0/json) | 2.21.0 | BSD-2-Clause | Test transitive |
| [python-dotenv](https://pypi.org/pypi/python-dotenv/1.2.4/json) | 1.2.4 | BSD-3-Clause | Transitive |
| [starlette](https://pypi.org/pypi/starlette/1.9.0/json) | 1.9.0 | BSD-3-Clause | Transitive |
| [typing_extensions](https://pypi.org/pypi/typing-extensions/4.16.0/json) | 4.16.0 | PSF-2.0 | Transitive |
| [typing-inspection](https://pypi.org/pypi/typing-inspection/0.4.4/json) | 0.4.4 | MIT | Transitive |
| [pip](https://pypi.org/pypi/pip/24.0/json) | 24.0 | MIT | Environment tooling |
| [setuptools](https://pypi.org/pypi/setuptools/79.0.1/json) | 79.0.1 | MIT | Build tooling; license text inspected |

## Compatibility and redistribution boundaries

The application uses these packages without modifying their source. The declared MIT, BSD, Apache-2.0 and PSF licenses permit their use with MIT application code subject to preserving their own terms. The MIT license in this repository applies to this project's authored code; it does not relicense dependencies.

Certifi's MPL-2.0 is a file-level weak-copyleft license, so the whole dependency set should not be described as exclusively permissive. No certifi source or CA bundle has been modified here. Keep its license and required notices; if distributing changed covered files, review the MPL source-availability requirements. This does not imply that unrelated application files must use MPL.

Each installed top-level distribution contains a license file under its `.dist-info` directory. Retain those files and relevant NOTICE/AUTHORS files in any distributed environment. Setuptools and pip also vendor components under their own notices; a tooling-inclusive distribution must retain those bundled notices. No vendor source has been copied into this repository. Python and any Docker base image have separate component licenses that must be checked for the final image.

Qloo data is not an open-source dependency. Its API output, imagery and marks remain subject to Qloo and third-party terms, as recorded in [SOURCES.md](SOURCES.md). Authored exploration rectangles and synthetic fixtures introduce no imported geodata license. A successful image build is not a completed container license audit.

## Reproduce the inventory

After installing the intended production and test dependencies, use Python's standard `importlib.metadata.distributions()` to enumerate `Name`, version, `License-Expression`, `License`, and distribution files containing `LICENSE` or `NOTICE`. Inspect text when metadata is ambiguous. Run `python -m pip check` to verify dependency constraints separately; that command does not verify licenses. Repeat inside the final Docker image, because this local inventory does not certify the container's entire component set.
