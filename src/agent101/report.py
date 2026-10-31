from html import escape

from agent101.models import ProcurementRequest, Product, ReportNarrative
from agent101.policy import validate_url


def render_report(
    request: ProcurementRequest,
    products: list[Product],
    narrative: ReportNarrative,
    *,
    demo: bool,
    run_id: str,
) -> str:
    rows = []

    for product in products:
        url = validate_url(product.source_url, request.allowed_domains)
        source = escape(url)

        if not demo:
            source = f'<a href="{source}" rel="noreferrer">Source page</a>'

        rows.append(
            "<tr>"
            f"<td>{escape(product.product_name)}</td>"
            f"<td>{escape(product.currency)} {product.price:,f}</td>"
            f"<td>{escape(product.price_excerpt)}</td>"
            f"<td>{source}</td>"
            "</tr>"
        )

    limitations = "".join(f"<li>{escape(item)}</li>" for item in narrative.limitations)

    label = (
        "OFFLINE DEMO — all products, URLs, and prices are invented."
        if demo
        else "LIVE RESEARCH — verify retailer details before buying."
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Procurement report</title>
<style>
body {{font-family:Arial,sans-serif;max-width:1100px;margin:40px auto;padding:20px;}}
table {{border-collapse:collapse;width:100%;}}
th,td {{border:1px solid #ccc;padding:12px;text-align:left;vertical-align:top;}}
th {{background:#eef2f6;}}
.notice {{background:#fff3cd;padding:14px;}}
</style>
</head>
<body>
<h1>{escape(request.product_name)}</h1>
<p class="notice">{escape(label)}</p>
<p>Run: {escape(run_id)}</p>
<table>
<caption>Eligible offers sorted by observed item price</caption>
<thead><tr>
<th scope="col">Product</th><th scope="col">Item price</th>
<th scope="col">Extracted price excerpt</th><th scope="col">Source</th>
</tr></thead>
<tbody>{"".join(rows)}</tbody>
</table>
<h2>Commentary — unverified assessment</h2>
<p>{escape(narrative.executive_summary)}</p>
<h2>Limitations</h2>
<ul>{limitations}</ul>
</body>
</html>
"""
