import urllib.request
import xml.etree.ElementTree as ET
import logging
import json
import os
import re

def get_news_standard(topic="Chhattisgarh"):
    """Fetch news using only standard library."""
    query = topic.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    news_items = []
    try:
        with urllib.request.urlopen(url) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            # Google News RSS structure: channel -> item -> title, link
            for item in root.findall(".//item")[:3]:
                title = item.find("title").text
                link = item.find("link").text
                
                # Clean title
                clean_title = title.split(" - ")[0]
                
                # Simple translation using a public API (might be unstable but standard-lib friendly)
                # We'll try a very simple translation approach or a placeholder if it fails
                hindi_explanation = translate_to_hindi(clean_title)
                
                news_items.append({
                    "english": clean_title,
                    "hindi": hindi_explanation,
                    "link": link
                })
    except Exception as e:
        print(f"Error fetching news: {e}")
        
    return news_items

def translate_to_hindi(text):
    """Simple translation using Google Translate public API (unsupported but works)."""
    try:
        safe_text = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=hi&dt=t&q={safe_text}"
        
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            # Result format is complex, but the first part is usually the translation
            return data[0][0][0]
    except Exception as e:
        print(f"Translation Error: {e}")
        return "Hindi translation unavailable (Check connection)."

if __name__ == "__main__":
    print("Testing News (Standard Lib)...")
    items = get_news_standard("Chhattisgarh")
    for item in items:
        print(f"EN: {item['english']}")
        print(f"HI: {item['hindi']}")
        print(f"LINK: {item['link']}")
        print("-" * 20)
