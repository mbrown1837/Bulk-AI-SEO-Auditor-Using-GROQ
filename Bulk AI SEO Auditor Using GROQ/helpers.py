from typing import List
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
from textwrap import wrap
import json
import streamlit as st
import re
import traceback
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize GROQ client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def display_wrapped_json(data, width=80):
    def wrap_str(s):
        return '\n'.join(wrap(s, width=width))

    def process_item(item):
        if isinstance(item, dict):
            return {k: process_item(v) for k, v in item.items()}
        elif isinstance(item, list):
            return [process_item(i) for i in item]
        elif isinstance(item, str):
            return wrap_str(item)
        else:
            return item

    wrapped_data = process_item(data)
    st.code(json.dumps(wrapped_data, indent=2), language='json')

def free_seo_audit(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        audit_result = {
            "http": {
                "status": response.status_code,
                "using_https": url.startswith("https://"),
                "response_time": f"{response.elapsed.total_seconds():.2f} seconds",
            },
            "metadata": {
                "title": soup.find("title").string if soup.find("title") else None,
                "title_length": len(soup.find("title").string) if soup.find("title") else 0,
                "description": soup.find("meta", {"name": "description"})["content"] if soup.find("meta", {"name": "description"}) else None,
                "description_length": len(soup.find("meta", {"name": "description"})["content"]) if soup.find("meta", {"name": "description"}) else 0,
            },
            "content": {
                "word_count": len(" ".join(soup.stripped_strings).split()),
                "h1_count": len(soup.find_all("h1")),
                "h2_count": len(soup.find_all("h2")),
                "h3_count": len(soup.find_all("h3")),
            },
            "links": {
                "total_links": len(soup.find_all("a")),
                "internal_links": len([link.get("href") for link in soup.find_all("a") if urlparse(link.get("href", "")).netloc == ""]),
                "external_links": len([link.get("href") for link in soup.find_all("a") if urlparse(link.get("href", "")).netloc != ""]),
            },
            "images": {
                "total_images": len(soup.find_all("img")),
                "images_without_alt": sum(1 for img in soup.find_all("img") if not img.get("alt")),
            },
        }

        return audit_result
    except Exception as ex:
        return {"error": str(ex)}

def ai_analysis(report):
    seo_audit_analysis_prompt = f"""You are an expert in SEO analysis.
    I will provide you with a [SEO_REPORT]
    and your task is to analyze and return a list of optimizations
    [SEO_REPORT]: {report}
    """

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "user", "content": seo_audit_analysis_prompt}
            ],
            max_tokens=4096
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in AI analysis: {str(e)}")
        return "Error occurred during AI analysis."

def fetch_url_content(url):
    return requests.get(url)

def get_http_info(response):
    return {
        "status": response.status_code,
        "using_https": response.url.startswith("https://"),
        "response_time": f"{response.elapsed.total_seconds():.2f} seconds",
    }

def full_seo_audit(url):
    audit_result = {}

    try:
        response = fetch_url_content(url)
        final_url = response.url
        using_https = final_url.startswith("https://")
        parsed_url = urlparse(url)
        input_type = "Domain" if parsed_url.path.strip("/") == "" else "URL with path"

        audit_result["Input"] = {
            "URL": url,
            "Input type": input_type,
        }

        audit_result["http"] = get_http_info(response)
        soup = BeautifulSoup(response.content, "html.parser")

        # Title analysis
        title_tag = soup.find("title")
        title_data = title_tag.string if title_tag else ""
        title_length = len(title_data)
        title_tag_number = len(soup.find_all("title"))
        audit_result["title"] = {
            "found": "Found" if title_tag else "Not found",
            "data": title_data,
            "length": title_length,
            "characters": len(title_data),
            "words": len(title_data.split()),
            "charPerWord": round(len(title_data) / len(title_data.split()), 2) if title_data else 0,
            "tag number": title_tag_number,
        }

        # Meta description analysis
        description_tag = soup.find("meta", {"name": "description"})
        description_data = description_tag["content"] if description_tag else ""
        description_length = len(description_data)
        meta_description_number = len(soup.find_all("meta", {"name": "description"}))
        audit_result["meta_description"] = {
            "found": "Found" if description_tag else "Not found",
            "data": description_data,
            "length": description_length,
            "characters": len(description_data),
            "words": len(description_data.split()),
            "charPerWord": round(len(description_data) / len(description_data.split()), 2) if description_data else 0,
            "number": meta_description_number,
        }

        # Metadata info
        metadata_info = {}
        charset_tag = soup.find("meta", {"charset": True})
        metadata_info["charset"] = charset_tag["charset"] if charset_tag else None
        canonical_tag = soup.find("link", {"rel": "canonical"})
        metadata_info["canonical"] = canonical_tag["href"] if canonical_tag else None
        favicon_tag = soup.find("link", {"rel": "icon"}) or soup.find("link", {"rel": "shortcut icon"})
        metadata_info["favicon"] = favicon_tag["href"] if favicon_tag else None
        viewport_tag = soup.find("meta", {"name": "viewport"})
        metadata_info["viewport"] = viewport_tag["content"] if viewport_tag else None
        keywords_tag = soup.find("meta", {"name": "keywords"})
        metadata_info["keywords"] = keywords_tag["content"] if keywords_tag else None
        locale_tag = soup.find("meta", {"property": "og:locale"})
        metadata_info["locale"] = locale_tag["content"] if locale_tag else None
        content_type_tag = soup.find("meta", {"property": "og:type"})
        metadata_info["contentType"] = content_type_tag["content"] if content_type_tag else None
        site_name_tag = soup.find("meta", {"property": "og:site_name"})
        metadata_info["site_name"] = site_name_tag["content"] if site_name_tag else None
        site_image_tag = soup.find("meta", {"property": "og:image"})
        metadata_info["site_image"] = site_image_tag["content"] if site_image_tag else None
        robots_tag = soup.find("meta", {"name": "robots"})
        metadata_info["robots"] = robots_tag["content"] if robots_tag else None
        hreflangs = []
        hreflang_tags = soup.find_all("link", {"rel": "alternate", "hreflang": True})
        for tag in hreflang_tags:
            hreflangs.append({"language": tag["hreflang"], "url": tag["href"]})
        metadata_info["hreflangs"] = hreflangs
        audit_result["metadata_info"] = metadata_info

        # Headings analysis
        headings = {"H1": 0, "H2": 0, "H3": 0, "H4": 0, "H5": 0, "H6": 0}
        for key in headings:
            headings[key] = len(soup.find_all(key.lower()))
        h1_content = soup.find("h1").text if soup.find("h1") else ""
        audit_result["Page Headings summary"] = {
            **headings,
            "H1 count": len(soup.find_all("h1")),
            "H1 Content": h1_content,
        }

        # Word count analysis
        text_content = " ".join(list(soup.stripped_strings))
        words = re.findall(r"\b\w+\b", text_content.lower())
        word_count_total = len(words)
        anchor_elements = soup.find_all("a")
        anchor_text = " ".join(a.text for a in anchor_elements if a.text.strip())
        anchor_text_words = len(anchor_text.split())
        anchor_percentage = round((anchor_text_words / word_count_total) * 100, 2)
        audit_result["word_count"] = {
            "total": word_count_total,
            "Corrected word count": word_count_total,
            "Anchor text words": anchor_text_words,
            "Anchor Percentage": anchor_percentage,
        }

        # Links analysis
        total_links = len(soup.find_all("a"))
        external_links = sum(1 for link in soup.find_all("a") if link.get("href", "").startswith("http"))
        internal_links = total_links - external_links
        nofollow_count = sum(1 for link in soup.find_all("a") if "nofollow" in link.get("rel", []))
        links = [
            {"href": link["href"], "text": link.text.strip()}
            for link in soup.find_all("a")
            if link.get("href")
        ]
        audit_result["links_summary"] = {
            "Total links": total_links,
            "External links": external_links,
            "Internal": internal_links,
            "Nofollow count": nofollow_count,
            "links": links,
        }

        # Image analysis
        images = soup.find_all("img")
        number_of_images = len(images)
        image_data = [
            {"src": img.get("src", ""), "alt": img.get("alt", "")} for img in images
        ]
        audit_result["images_analysis"] = {
            "summary": {
                "total": number_of_images,
                "No src tag": sum(1 for img in images if not img.get("src")),
                "No alt tag": sum(1 for img in images if not img.get("alt")),
            },
            "data": image_data,
        }

    except Exception as ex:
        print(f"Error in full_seo_audit: {str(ex)}\nStack trace: {traceback.format_exc()}")
        return {"error": str(ex)}

    return audit_result