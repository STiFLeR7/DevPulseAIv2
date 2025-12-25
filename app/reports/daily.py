from datetime import datetime, timedelta
from app.persistence.client import db
from app.core.logger import logger

class DailyReportGenerator:
    def generate_html_report(self) -> str:
        """
        Queries Supabase for the last 24h (Strict) and formats into categories:
        New Topics, New Trends, New Repos, Updates, Blogs, Insights, Summary.
        """
        # Strict 24h window
        time_threshold = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        
        # 1. Fetch Raw Signals
        signals_res = db.get_client().table("raw_signals").select("*").gte("created_at", time_threshold).execute()
        signals = signals_res.data if signals_res.data else []
        
        # 2. Fetch Intelligence
        intel_res = db.get_client().table("processed_intelligence").select("*").gte("created_at", time_threshold).execute()
        intel_data = intel_res.data if intel_res.data else []
        
        # 3. Categorize
        categories = {
            "New Topics": [],
            "New Trends": [],
            "New Repos": [],
            "Updates": [],
            "Blogs": [],
            "Insights": [],
            "Summary": [] # General summaries if not fitting elsewhere
        }
        
        # Mapping helpers
        intel_map = {}
        for i in intel_data:
            s_id = i['signal_id']
            if s_id not in intel_map: intel_map[s_id] = []
            intel_map[s_id].append(i)
            
            # Direct Trend Injection
            if i['agent_name'] == 'trend_detection':
                categories["New Trends"].append(i['output_data'])

        for s in signals:
            payload = s['payload']
            source = s['source']
            my_intel = intel_map.get(s['id'], [])
            
            # Basic info
            item = {
                "title": payload.get('title', 'Untitled'),
                "url": payload.get('url', '#'),
                "summary": next((x['output_data'].get('summary_text') for x in my_intel if x['agent_name'] == 'summarization'), "No summary."),
                "relevance": next((x['output_data'].get('score') for x in my_intel if x['agent_name'] == 'relevance'), 0),
                "risk": next((x['output_data'].get('risk_level') for x in my_intel if x['agent_name'] == 'risk_analysis'), "UNKNOWN")
            }
            
            # Logic for Categorization
            if source == 'github':
                categories["New Repos"].append(item)
            elif source == 'medium':
                categories["Blogs"].append(item)
            elif source == 'huggingface':
                categories["Updates"].append(item) # HF models often updates
            elif source == 'arxiv':
                categories["Insights"].append(item) # Research = Insights
            elif source == 'twitter':
                categories["New Topics"].append(item) # X = New Topics
            else:
                categories["Summary"].append(item)

        # 4. Generate HTML
        return self._render_html(categories, datetime.utcnow().strftime('%Y-%m-%d'))

    def _render_html(self, categories, date_str):
        # Premium Tech Vibe (Google-ish: Roboto, Cards, Clean)
        style = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
            body { font-family: 'Roboto', sans-serif; background-color: #f1f3f4; color: #202124; margin: 0; padding: 0; }
            .container { max-width: 650px; margin: 20px auto; background: #ffffff; border-radius: 8px; box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15); overflow: hidden; }
            
            .header { background: #ffffff; padding: 30px 40px; border-bottom: 1px solid #e0e0e0; }
            .header h1 { font-size: 24px; font-weight: 400; color: #202124; margin: 0 0 10px; }
            .header p { font-size: 14px; color: #5f6368; margin: 0; }
            
            .greeting-box { padding: 20px 40px; background: #e8f0fe; color: #1967d2; font-size: 16px; font-weight: 500; }
            
            .section { padding: 20px 40px; border-bottom: 1px solid #f1f3f4; }
            .section:last-child { border-bottom: none; }
            
            .section-title { font-size: 14px; font-weight: 700; color: #5f6368; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 15px; display: flex; align-items: center; }
            .section-title span { margin-left: auto; font-size: 12px; font-weight: 400; color: #80868b; }

            /* Google-like Colors for Categories */
            .c-blue { color: #1a73e8; }   /* X/Twitter */
            .c-red { color: #d93025; }    /* GitHub (custom choice vs grey) */
            .c-yellow { color: #f9ab00; } /* HF */
            .c-green { color: #188038; }  /* ArXiv */
            .c-grey { color: #5f6368; }   /* Summary/Medium */
            
            .item { margin-bottom: 20px; }
            .item:last-child { margin-bottom: 0; }
            
            .item-title { display: block; font-size: 16px; font-weight: 400; color: #1a73e8; text-decoration: none; margin-bottom: 4px; }
            .item-title:hover { text-decoration: underline; }
            
            .item-meta { font-size: 12px; color: #5f6368; margin-bottom: 8px; display: flex; gap: 10px; align-items: center; }
            
            .item-summary { font-size: 14px; color: #3c4043; line-height: 1.5; }
            
            .badge { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 500; background: #f1f3f4; color: #5f6368; }
            .badge-risk { background: #fce8e6; color: #c5221f; }
            .badge-growth { background: #e6f4ea; color: #137333; }
            
            .footer { background: #f8f9fa; padding: 20px 40px; text-align: center; font-size: 12px; color: #5f6368; border-top: 1px solid #e0e0e0; }
        </style>
        """
        
        html = f"""<!DOCTYPE html><html><head>{style}</head><body>
        <div class="container">
            <div class="header">
                <h1>DevPulseAI Daily Digest</h1>
                <p>{date_str} • Automated Intelligence</p>
            </div>
            <div class="greeting-box">
                Hey Hill Patel, here is your daily digest!
            </div>
        """
        
        # Mapping for Titles and Colors
        # X=Blue, GitHub=Red (or Grey), HF=Yellow, ArXiv=Green, Medium=Grey
        cat_config = {
            "New Trends": {"color": "c-grey", "icon": "📈"},
            "New Topics": {"color": "c-blue", "icon": "🐦"}, # X
            "New Repos": {"color": "c-red", "icon": "💻"}, # GitHub (Red implies Code/Git)
            "Updates": {"color": "c-yellow", "icon": "🤗"}, # HF
            "Insights": {"color": "c-green", "icon": "📄"}, # ArXiv
            "Blogs": {"color": "c-grey", "icon": "✍️"}, # Medium
            "Summary": {"color": "c-grey", "icon": "📋"},
        }

        order = ["New Trends", "New Topics", "New Repos", "Updates", "Insights", "Blogs", "Summary"]
        
        for cat in order:
            items = categories.get(cat, [])
            if not items: continue
            
            conf = cat_config.get(cat, {"color": "c-grey", "icon": ""})
            color_class = conf["color"]
            icon = conf["icon"]
            
            html += f'<div class="section"><div class="section-title {color_class}">{icon} {cat} <span>{len(items)} updates</span></div>'
            
            if cat == "New Trends":
                for t in items:
                    name = t.get('trend_name', 'Unknown')
                    growth = t.get('growth_rate', 'Stable')
                    html += f"""
                    <div class="item">
                        <div style="font-size: 16px; color: #202124;">{name} <span class="badge badge-growth">{growth}</span></div>
                    </div>"""
            else:
                for item in items:
                    risk_badge = f'<span class="badge badge-risk">RISK: {item["risk"]}</span>' if item["risk"] == "HIGH" else ""
                    html += f"""
                    <div class="item">
                        <a href="{item['url']}" class="item-title">{item['title']}</a>
                        <div class="item-meta">
                            <span>Relevance: {item['relevance']}</span>
                            {risk_badge}
                        </div>
                        <div class="item-summary">{item['summary']}</div>
                    </div>
                    """
            html += '</div>'

        html += f'<div class="footer">Generated by DevPulseAI v2 on Google Cloud Run</div></div></body></html>'
        return html
