import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from io import BytesIO
import concurrent.futures
import time
import ssl
import socket
import urllib3
from urllib.parse import urlparse, urljoin
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SitemapExtractor:
    @staticmethod
    def extract_urls_from_sitemap(sitemap_url, recursive=True, max_depth=3):
        """
        Recursively extract URLs from XML sitemap, handling nested sitemaps
        
        :param sitemap_url: URL of the sitemap
        :param recursive: Whether to follow sitemap indexes
        :param max_depth: Maximum recursion depth
        :return: List of unique URLs
        """
        def fetch_sitemap_content(url):
            try:
                response = requests.get(url, verify=False, timeout=10)
                return response.content
            except Exception as e:
                st.error(f"Error fetching sitemap {url}: {e}")
                return None

        def parse_sitemap(content, base_url):
            try:
                root = ET.fromstring(content)
                namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                
                # Extract URLs from standard sitemap
                urls = root.findall('.//ns:loc', namespace)
                extracted_urls = [url.text.strip() for url in urls if url.text]
                
                # Check for sitemap indexes if recursive
                if recursive and max_depth > 0:
                    sitemap_indexes = root.findall('.//ns:sitemap/ns:loc', namespace)
                    for sitemap_loc in sitemap_indexes:
                        nested_sitemap_url = sitemap_loc.text.strip()
                        nested_content = fetch_sitemap_content(nested_sitemap_url)
                        if nested_content:
                            nested_urls = parse_sitemap(nested_content, nested_sitemap_url)
                            extracted_urls.extend(nested_urls)
                
                return extracted_urls
            except ET.ParseError:
                st.error(f"Could not parse sitemap: {base_url}")
                return []
            except Exception as e:
                st.error(f"Unexpected error parsing sitemap: {e}")
                return []

        # Start extraction
        initial_content = fetch_sitemap_content(sitemap_url)
        if initial_content:
            return parse_sitemap(initial_content, sitemap_url)
        return []

class URLStatusChecker:
    # [Previous URLStatusChecker implementation remains the same]
    # ... (keep all the previous code for URLStatusChecker)

def main():
    st.title("🌐 SitemapSage Pro: Advanced URL Status Checker")
    
    # Tabs for different input methods
    tab1, tab2 = st.tabs(["Manual URLs", "Sitemap Extraction"])
    
    with tab1:
        st.subheader("Manual URL Entry")
        # [Previous manual URL input section remains the same]
        # ... (keep the existing manual URL input code)
    
    with tab2:
        st.subheader("Extract URLs from Sitemap")
        
        # Sitemap URL Input
        sitemap_url = st.text_input(
            "Enter Sitemap URL", 
            placeholder="https://example.com/sitemap.xml"
        )
        
        # Sitemap Extraction Options
        col1, col2 = st.columns(2)
        with col1:
            recursive_extraction = st.checkbox(
                "Recursive Extraction", 
                value=True, 
                help="Extract URLs from nested sitemaps"
            )
        with col2:
            max_depth = st.number_input(
                "Max Recursion Depth", 
                min_value=1, 
                max_value=5, 
                value=3,
                help="Maximum depth for nested sitemap extraction"
            )
        
        # Extract Sitemap URLs Button
        if st.button("🔍 Extract URLs from Sitemap"):
            if sitemap_url:
                with st.spinner('Extracting URLs from Sitemap...'):
                    extracted_urls = SitemapExtractor.extract_urls_from_sitemap(
                        sitemap_url, 
                        recursive=recursive_extraction, 
                        max_depth=max_depth
                    )
                
                if extracted_urls:
                    st.success(f"Extracted {len(extracted_urls)} URLs")
                    
                    # Display extracted URLs
                    st.dataframe(pd.DataFrame(extracted_urls, columns=['URLs']))
                    
                    # Option to proceed with URL status check
                    if st.button("Check Status of Extracted URLs"):
                        with st.spinner('Checking URL Status...'):
                            # Use the previously defined URLStatusChecker
                            checker = URLStatusChecker(
                                max_workers=10, 
                                timeout=10,
                                sampling_rate=1.0,
                                batch_size=None
                            )
                            results_df = checker.batch_url_status_check(extracted_urls)
                        
                        # [Rest of the results display code remains the same]
                        # ... (keep the existing results display and export code)
                else:
                    st.warning("No URLs could be extracted from the sitemap")
            else:
                st.warning("Please enter a sitemap URL")

if __name__ == "__main__":
    main()
