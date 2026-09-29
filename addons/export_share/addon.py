"""Export & Package Sharing addon: moved the standalone-HTML / SNS-image /
.edsys package export & import endpoints out of app/server/api.py.

Left in core (unchanged) on purpose:
- app/services/export_service.py -- the service module itself. It also
  backs GET /api/system/{id}/orrery (the in-app Orrery tab, via
  build_interactive_orrery), which is a core UI view, not an export/share
  action, so that route stays in api.py and keeps importing directly from
  export_service.py regardless of whether this addon is enabled.
- app/live/rhino/tracker.py::extract_rhino_mining_sites -- a shared helper
  also used by the core system-detail endpoint.

Enabled by default since this was previously an always-on core feature;
disabling it removes the export/share endpoints listed below, but never
touches the Orrery tab or core system browsing.
"""
import json
import subprocess
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import HTMLResponse, Response, JSONResponse
from pydantic import BaseModel

from app.config import BASE_DIR, EXPORTS_DIR
from app.db.database import get_db_connection, get_mining_sites
from app.live.rhino.tracker import extract_rhino_mining_sites
from app.services.export_service import (
    generate_standalone_html,
    generate_share_snippet,
    generate_summary_png_card,
    extract_package_from_png,
    create_edsys_package,
    import_edsys_package,
    verify_package_signature,
)


class ExportPackageRequest(BaseModel):
    system_addresses: List[int]
    cmdr_name: Optional[str] = "Explorer"
    notes: Optional[str] = ""
    consent_token: bool = False


class SavePackageLocalRequest(BaseModel):
    system_addresses: List[int]
    cmdr_name: Optional[str] = "Explorer"
    notes: Optional[str] = ""
    consent_token: bool = False
    reveal: Optional[bool] = True


class RevealPathRequest(BaseModel):
    file_path: str


class ImportExecuteRequest(BaseModel):
    package: Optional[dict] = None
    package_data: Optional[dict] = None
    overwrite: Optional[bool] = False
    consent_token: bool = False


class OpenLocationRequest(BaseModel):
    path: Optional[str] = None


def _safe_filename(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in (name or "system"))


def register(ctx):
    router = APIRouter()

    @router.get("/export/html/{system_address}")
    def export_standalone_html_endpoint(
        system_address: int,
        cmdr_name: Optional[str] = None,
        is_anonymous: bool = False,
        lang: str = "ja"
    ):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM systems WHERE system_address = ?", (system_address,))
        sys_row = c.fetchone()
        if not sys_row:
            conn.close()
            return JSONResponse({"error": "System not found"}, status_code=404)

        if (sys_row["visit_count"] or 0) == 0:
            conn.close()
            err_msg = "Cannot export Web Share HTML for unvisited external reference systems." if lang == "en" else "外部参照（未訪問）星系のため、Web共有HTMLのエクスポートは行えません。"
            return JSONResponse({"error": err_msg}, status_code=403)

        system_data = dict(sys_row)
        c.execute("SELECT * FROM bodies WHERE system_address = ? ORDER BY distance_from_arrival_ls ASC, body_id ASC", (system_address,))
        bodies = [dict(r) for r in c.fetchall()]

        c.execute("SELECT * FROM surface_mining_activities WHERE system_address = ? ORDER BY timestamp DESC", (system_address,))
        raw_mining = [dict(r) for r in c.fetchall()]
        db_sites = get_mining_sites(conn, system_address)
        if db_sites:
            mining_sites = db_sites
        else:
            mining_sites = extract_rhino_mining_sites(raw_mining, include_raw=True)

        c.execute("SELECT * FROM body_bookmarks WHERE system_address = ?", (system_address,))
        bookmarks = [dict(r) for r in c.fetchall()]
        conn.close()

        html_content = generate_standalone_html(
            system_data=system_data,
            bodies=bodies,
            mining_sites=mining_sites,
            bookmarks=bookmarks,
            cmdr_name=cmdr_name,
            is_anonymous=is_anonymous,
            lang=lang
        )
        safe_sys_name = _safe_filename(system_data.get("star_system", "system"))
        filename = f"{safe_sys_name}_share.html"

        local_file_path = EXPORTS_DIR / filename
        try:
            local_file_path.write_text(html_content, encoding="utf-8")
        except Exception as e:
            print(f"Failed to save local export file {local_file_path}: {e}")

        return HTMLResponse(
            content=html_content,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Export-Path": str(local_file_path.resolve()),
                "Access-Control-Expose-Headers": "X-Export-Path, Content-Disposition"
            }
        )

    @router.get("/export/snippet/{system_address}")
    def export_snippet_endpoint(system_address: int, lang: str = "ja"):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM systems WHERE system_address = ?", (system_address,))
        sys_row = c.fetchone()
        if not sys_row:
            conn.close()
            return JSONResponse({"error": "System not found"}, status_code=404)

        system_data = dict(sys_row)
        c.execute("SELECT * FROM bodies WHERE system_address = ? ORDER BY distance_from_arrival_ls ASC, body_id ASC", (system_address,))
        bodies = [dict(r) for r in c.fetchall()]
        conn.close()

        snippet = generate_share_snippet(system_data, bodies, lang=lang)
        return {"status": "ok", "system_address": system_address, "snippet": snippet}

    @router.get("/export/image/{system_address}")
    def export_summary_image_endpoint(system_address: int, lang: str = "ja"):
        """Generates a ComfyUI-style SNS summary PNG card (1200x630) with embedded
        .edsys package metadata. Deliberately omits Orrery and Credit payout
        values to entice viewers to drop into the app."""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM systems WHERE system_address = ?", (system_address,))
        sys_row = c.fetchone()
        if not sys_row:
            conn.close()
            return JSONResponse({"error": "System not found"}, status_code=404)

        if (sys_row["visit_count"] or 0) == 0:
            conn.close()
            err_msg = "Cannot export summary image for unvisited external reference systems." if lang == "en" else "外部参照（未訪問）星系のため、サマリー画像のエクスポートは行えません。"
            return JSONResponse({"error": err_msg}, status_code=403)

        system_data = dict(sys_row)
        c.execute("SELECT * FROM bodies WHERE system_address = ? ORDER BY distance_from_arrival_ls ASC, body_id ASC", (system_address,))
        bodies = [dict(r) for r in c.fetchall()]

        cmdr_name = "Explorer"
        try:
            c.execute("SELECT commander_name FROM commanders ORDER BY last_seen DESC LIMIT 1")
            cmdr_row = c.fetchone()
            if cmdr_row and cmdr_row["commander_name"]:
                cmdr_name = cmdr_row["commander_name"]
        except Exception:
            pass

        package = create_edsys_package(
            conn,
            system_addresses=[system_address],
            cmdr_name=cmdr_name,
            notes="Exported via Summary PNG Card"
        )
        conn.close()

        png_bytes = generate_summary_png_card(
            system_data=system_data,
            bodies=bodies,
            package_dict=package,
            lang=lang
        )

        safe_sys_name = _safe_filename(system_data.get("star_system", "system"))
        filename = f"{safe_sys_name}_summary.png"
        local_file_path = EXPORTS_DIR / filename
        try:
            local_file_path.write_bytes(png_bytes)
        except Exception as e:
            print(f"Failed to save local export image {local_file_path}: {e}")

        return Response(
            content=png_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Export-Path": str(local_file_path.resolve()),
                "Access-Control-Expose-Headers": "X-Export-Path, Content-Disposition"
            }
        )

    @router.post("/export/open_location")
    def open_export_location(payload: OpenLocationRequest):
        target = Path(payload.path) if payload.path else EXPORTS_DIR
        if not target.is_absolute():
            target = (BASE_DIR / target).resolve()

        if not target.exists():
            target = EXPORTS_DIR

        try:
            if target.is_file():
                subprocess.Popen(f'explorer.exe /select,"{target}"')
            else:
                subprocess.Popen(f'explorer.exe "{target}"')
            return {"success": True, "opened": str(target)}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.post("/export/package")
    def export_package_endpoint(payload: ExportPackageRequest):
        if not payload.consent_token:
            return JSONResponse({"error": "エクスポートには注意事項への同意が必要です。"}, status_code=400)
        if not payload.system_addresses:
            return JSONResponse({"error": "対象星系が選択されていません。"}, status_code=400)

        conn = get_db_connection()
        try:
            placeholders = ",".join("?" * len(payload.system_addresses))
            c = conn.cursor()
            c.execute(f"SELECT star_system FROM systems WHERE system_address IN ({placeholders}) AND (visit_count IS NULL OR visit_count = 0)", payload.system_addresses)
            ext_rows = c.fetchall()
            if ext_rows:
                ext_names = [r["star_system"] for r in ext_rows]
                return JSONResponse({"error": f"外部参照（未訪問）星系 ({', '.join(ext_names)}) はパッケージ書き出しできません。"}, status_code=403)

            package = create_edsys_package(
                conn,
                system_addresses=payload.system_addresses,
                cmdr_name=payload.cmdr_name or "Explorer",
                notes=payload.notes or ""
            )
            return package
        finally:
            conn.close()

    @router.post("/export/package/save-local")
    def export_package_save_local(payload: SavePackageLocalRequest):
        if not payload.consent_token:
            return JSONResponse({"error": "エクスポートには注意事項への同意が必要です。"}, status_code=400)
        if not payload.system_addresses:
            return JSONResponse({"error": "対象星系が選択されていません。"}, status_code=400)

        conn = get_db_connection()
        try:
            placeholders = ",".join("?" * len(payload.system_addresses))
            c = conn.cursor()
            c.execute(f"SELECT star_system FROM systems WHERE system_address IN ({placeholders}) AND (visit_count IS NULL OR visit_count = 0)", payload.system_addresses)
            ext_rows = c.fetchall()
            if ext_rows:
                ext_names = [r["star_system"] for r in ext_rows]
                return JSONResponse({"error": f"外部参照（未訪問）星系 ({', '.join(ext_names)}) はパッケージ書き出しできません。"}, status_code=403)

            package = create_edsys_package(
                conn,
                system_addresses=payload.system_addresses,
                cmdr_name=payload.cmdr_name or "Explorer",
                notes=payload.notes or ""
            )
            systems = package.get("systems", [])
            if systems and systems[0].get("star_system"):
                safe_name = _safe_filename(systems[0]["star_system"])
            else:
                safe_name = "System_Export"

            downloads_dir = Path.home() / "Downloads"
            if not downloads_dir.exists():
                downloads_dir = Path("./exports")
                downloads_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{safe_name}.edsys"
            out_path = downloads_dir / filename
            counter = 1
            while out_path.exists():
                out_path = downloads_dir / f"{safe_name}_{counter}.edsys"
                counter += 1

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(package, f, ensure_ascii=False, indent=2)

            if payload.reveal:
                try:
                    subprocess.Popen(f'explorer /select,"{str(out_path.resolve())}"', shell=True)
                except Exception as e:
                    print(f"Could not open explorer: {e}")

            return {
                "status": "success",
                "saved_path": str(out_path.resolve()),
                "filename": out_path.name,
                "directory": str(downloads_dir.resolve()),
                "package": package
            }
        finally:
            conn.close()

    @router.post("/system/reveal-file")
    def reveal_file_in_explorer(payload: RevealPathRequest):
        p = Path(payload.file_path).resolve()
        if p.exists():
            try:
                subprocess.Popen(f'explorer /select,"{str(p)}"', shell=True)
                return {"status": "ok"}
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse({"error": "File not found"}, status_code=404)

    @router.post("/import/package/preview")
    def import_package_preview(package: dict):
        pkg = package.get("package_data") or package.get("package") or package
        is_valid, reason = verify_package_signature(pkg)
        metadata = pkg.get("metadata", {})
        systems = pkg.get("systems", [])
        preview_systems = []
        total_bodies = 0
        for s in systems:
            b_count = len(s.get("bodies", []))
            total_bodies += b_count
            preview_systems.append({
                "system_address": s.get("system_address"),
                "star_system": s.get("star_system"),
                "main_star_type": s.get("main_star_type"),
                "body_count": b_count,
                "mining_count": len(s.get("surface_mining", [])),
                "bookmark_count": len(s.get("bookmarks", []))
            })
        cmdr = metadata.get("cmdr_name", "Unknown")
        exp_at = metadata.get("exported_at", "")
        notes = metadata.get("notes", "")
        return {
            "is_valid": is_valid,
            "signature_valid": is_valid,
            "validation_message": reason,
            "cmdr_name": cmdr,
            "created_by": cmdr,
            "exported_at": exp_at,
            "export_date": exp_at,
            "system_count": len(systems),
            "total_bodies": total_bodies,
            "notes": notes,
            "systems": preview_systems
        }

    @router.post("/import/png")
    async def import_png_preview_endpoint(file: UploadFile = File(...)):
        """Extracts embedded .edsys package from an uploaded ComfyUI-style PNG
        summary card, then returns the package preview structure."""
        try:
            contents = await file.read()
            pkg = extract_package_from_png(contents)
            if not pkg:
                return JSONResponse(
                    {"error": "PNG画像内に有効なED Journal Analyzerメタデータ（ed_journal_data）が見つかりませんでした。"},
                    status_code=400
                )
            preview = import_package_preview(pkg)
            preview["package"] = pkg
            return preview
        except Exception as e:
            return JSONResponse({"error": f"PNGの解析に失敗しました: {str(e)}"}, status_code=400)

    @router.post("/import/package/execute")
    def import_package_execute(payload: ImportExecuteRequest):
        if not payload.consent_token:
            return JSONResponse({"error": "インポートには注意事項への同意が必要です。"}, status_code=400)

        pkg = payload.package or payload.package_data
        if not pkg:
            return JSONResponse({"error": "パッケージデータが存在しません。"}, status_code=400)

        conn = get_db_connection()
        try:
            res = import_edsys_package(conn, pkg, overwrite=payload.overwrite, allow_invalid_signature=True)
            return res
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        finally:
            conn.close()

    # Reclaims the original /api/export/*, /api/system/reveal-file,
    # /api/import/* paths (no /api/addons/... prefix) so existing frontend
    # call sites keep working unmodified.
    ctx.add_api_router(router, prefix="/api")
