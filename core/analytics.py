"""
core/analytics.py - Processing History Analytics & Multi-Format Report Generator.
"""

import csv
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class AnalyticsTracker:
    """Collects metrics during a run and exports reports in CSV, JSON, and HTML."""

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.reset()

    def reset(self):
        self.start_time = time.time()
        self.end_time = None
        self.total_files = 0
        self.processed_count = 0
        self.skipped_count = 0
        self.duplicate_count = 0
        self.error_count = 0
        self.total_bytes = 0
        self.resolution_counts: Dict[str, int] = {}
        self.codec_counts: Dict[str, int] = {}
        self.media_type_counts: Dict[str, int] = {}
        self.release_group_counts: Dict[str, int] = {}
        self.records: List[Dict[str, Any]] = []

    def record_file(
        self,
        source_name: str,
        target_name: str,
        status: str,
        size_bytes: int = 0,
        parsed_info: Dict[str, Any] = None,
        error_msg: str = ""
    ):
        """Records the outcome of a single processed file."""
        self.total_bytes += size_bytes
        info = parsed_info or {}

        res = info.get("Resolution") or "Unknown"
        self.resolution_counts[res] = self.resolution_counts.get(res, 0) + 1

        codec = info.get("VideoCodec") or "Unknown"
        self.codec_counts[codec] = self.codec_counts.get(codec, 0) + 1

        mtype = info.get("MediaType") or "Episode"
        self.media_type_counts[mtype] = self.media_type_counts.get(mtype, 0) + 1

        group = info.get("ReleaseGroup") or "None"
        self.release_group_counts[group] = self.release_group_counts.get(group, 0) + 1

        if status == "success":
            self.processed_count += 1
        elif status == "skipped":
            self.skipped_count += 1
        elif status == "duplicate":
            self.duplicate_count += 1
        elif status == "error":
            self.error_count += 1

        self.records.append({
            "timestamp": datetime.now().isoformat(),
            "source": source_name,
            "target": target_name,
            "status": status,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "resolution": res,
            "codec": codec,
            "media_type": mtype,
            "group": group,
            "error": error_msg
        })

    def get_summary(self) -> Dict[str, Any]:
        """Returns consolidated metrics summary."""
        duration = (self.end_time or time.time()) - self.start_time
        fps = (self.processed_count + self.skipped_count) / max(duration, 0.001)
        mbps = (self.total_bytes / (1024 * 1024)) / max(duration, 0.001)

        return {
            "duration_seconds": round(duration, 2),
            "files_per_sec": round(fps, 2),
            "mb_per_sec": round(mbps, 2),
            "total_files": self.total_files,
            "processed": self.processed_count,
            "skipped": self.skipped_count,
            "duplicates": self.duplicate_count,
            "errors": self.error_count,
            "total_size_gb": round(self.total_bytes / (1024 ** 3), 3),
            "resolutions": self.resolution_counts,
            "codecs": self.codec_counts,
            "media_types": self.media_type_counts,
            "release_groups": self.release_group_counts
        }

    def export_csv(self, filename: Optional[str] = None) -> Path:
        """Exports session records to CSV."""
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        out_path = self.reports_dir / filename

        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["timestamp", "source", "target", "status", "size_mb", "resolution", "codec", "media_type", "group", "error"]
            )
            writer.writeheader()
            for rec in self.records:
                writer.writerow(rec)

        return out_path

    def export_json(self, filename: Optional[str] = None) -> Path:
        """Exports summary and detailed records to JSON."""
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        out_path = self.reports_dir / filename

        data = {
            "summary": self.get_summary(),
            "records": self.records
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        return out_path

    def export_html(self, filename: Optional[str] = None) -> Path:
        """Exports standalone modern HTML dashboard report."""
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        out_path = self.reports_dir / filename

        summary = self.get_summary()

        rows_html = "".join([
            f"""<tr>
                <td>{r['timestamp'].split('T')[-1][:8]}</td>
                <td>{r['source']}</td>
                <td>{r['target']}</td>
                <td><span class="badge {r['status']}">{r['status'].upper()}</span></td>
                <td>{r['resolution']}</td>
                <td>{r['codec']}</td>
                <td>{r['size_mb']} MB</td>
            </tr>""" for r in self.records[:500]
        ])

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Organizer Pro - Processing Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .header {{ background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 20px; border-left: 6px solid #3b82f6; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: #1e293b; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #334155; }}
        .stat-val {{ font-size: 24px; font-weight: bold; color: #38bdf8; }}
        .stat-label {{ font-size: 13px; color: #94a3b8; text-transform: uppercase; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 10px; overflow: hidden; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #334155; font-size: 13px; }}
        th {{ background: #0f172a; color: #94a3b8; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
        .success {{ background: #065f46; color: #34d399; }}
        .skipped {{ background: #854d0e; color: #facc15; }}
        .duplicate {{ background: #6b21a8; color: #c084fc; }}
        .error {{ background: #991b1b; color: #f87171; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 Smart File Organizer Pro - Run Report</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Size: {summary['total_size_gb']} GB | Duration: {summary['duration_seconds']}s</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card"><div class="stat-val">{summary['processed']}</div><div class="stat-label">Processed</div></div>
        <div class="stat-card"><div class="stat-val">{summary['skipped']}</div><div class="stat-label">Skipped</div></div>
        <div class="stat-card"><div class="stat-val">{summary['duplicates']}</div><div class="stat-label">Duplicates</div></div>
        <div class="stat-card"><div class="stat-val">{summary['errors']}</div><div class="stat-label">Errors</div></div>
        <div class="stat-card"><div class="stat-val">{summary['files_per_sec']}/s</div><div class="stat-label">Speed</div></div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Time</th><th>Source</th><th>Destination</th><th>Status</th><th>Resolution</th><th>Codec</th><th>Size</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
</body>
</html>"""

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return out_path
