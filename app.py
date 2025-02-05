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

        def parse_sitemap(content, base_url, current_depth=0):
            try:
                root = ET.fromstring(content)
                namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                
                # Extract URLs from standard sitemap
                urls = root.findall('.//ns:loc', namespace)
                extracted_urls = [url.text.strip() for url in urls if url.text]
                
                # Check for sitemap indexes if recursive
                if recursive and current_depth < max_depth:
                    sitemap_indexes = root.findall('.//ns:sitemap/ns:loc', namespace)
                    for sitemap_loc in sitemap_indexes:
                        nested_sitemap_url = sitemap_loc.text.strip()
                        nested_content = fetch_sitemap_content(nested_sitemap_url)
                        if nested_content:
                            nested_urls = parse_sitemap(nested_content, nested_sitemap_url, current_depth + 1)
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
            return list(set(parse_sitemap(initial_content, sitemap_url)))  # Remove duplicates
        return []

# [Rest of the previous implementation remains the same, including URLStatusChecker class]

def main():
    # [Previous implementation remains the same up to the last part]
    
    # Complete the last part of the Sitemap Extraction tab
    with tab2:
        # [Previous code remains the same]
        
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
            
            # Results display
            st.subheader("URL Status Results")
            
            def color_status(status):
                status_colors = {
                    'Healthy': 'background-color: lightgreen',
                    'Unhealthy': 'background-color: salmon',
                    'Error': 'background-color: lightyellow'
                }
                return status_colors.get(status, '')
            
            styled_df = results_df.style.applymap(color_status, subset=['status'])
            st.dataframe(styled_df)
            
            # Detailed Insights
            st.subheader("URL Health Insights")
            
            # Summary Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total URLs Processed", len(results_df))
            with col2:
                healthy_urls = results_df[results_df['status'] == 'Healthy']
                st.metric("Healthy URLs", len(healthy_urls))
            with col3:
                avg_response_time = results_df['response_time'].mean()
                st.metric("Avg Response Time", f"{avg_response_time:.2f}s")
            
            # Export Options
            col1, col2 = st.columns(2)
            with col1:
                csv = results_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="sitemap_url_status_results.csv",
                    mime="text/csv"
                )
            with col2:
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    results_df.to_excel(writer, index=False)
                st.download_button(
                    label="📊 Download Excel",
                    data=excel_buffer.getvalue(),
                    file_name="sitemap_url_status_results.xlsx",
                    mime="application/vnd.ms-excel"
                )

if __name__ == "__main__":
    main()
