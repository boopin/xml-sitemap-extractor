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

class URLStatusChecker:
    def __init__(self, max_workers=10, timeout=10, sampling_rate=1.0, batch_size=None):
        """
        Initialize URL Status Checker with advanced configuration
        
        :param max_workers: Maximum concurrent workers for URL checking
        :param timeout: Request timeout in seconds
        :param sampling_rate: Percentage of URLs to check (0.0 - 1.0)
        :param batch_size: Maximum number of URLs to process in a single batch
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.sampling_rate = sampling_rate
        self.batch_size = batch_size
        self.logger = logging.getLogger(__name__)

    def _sample_urls(self, urls):
        """
        Sample URLs based on sampling rate
        
        :param urls: List of URLs
        :return: Sampled URLs
        """
        if self.sampling_rate >= 1.0:
            return urls
        
        sample_count = max(1, int(len(urls) * self.sampling_rate))
        return random.sample(urls, sample_count)

    def _check_url_status(self, url):
        """
        Comprehensive URL status checker with advanced error handling
        
        :param url: URL to check
        :return: Dictionary with URL status information
        """
        result = {
            'original_url': url,
            'status': 'Unchecked',
            'http_code': None,
            'redirect_chain': [],
            'ssl_valid': False,
            'response_time': None,
            'content_type': None,
            'server': None,
            'error': None
        }

        try:
            start_time = time.time()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }

            response = requests.get(
                url, 
                headers=headers, 
                allow_redirects=True, 
                timeout=self.timeout,
                verify=False
            )

            response_time = time.time() - start_time
            result.update({
                'http_code': response.status_code,
                'status': 'Healthy' if 200 <= response.status_code < 400 else 'Unhealthy',
                'redirect_chain': [r.url for r in response.history] + [response.url],
                'response_time': round(response_time, 3),
                'content_type': response.headers.get('Content-Type', 'Unknown'),
                'server': response.headers.get('Server', 'Unknown')
            })

            # SSL Certificate Check
            try:
                parsed_url = urlparse(url)
                hostname = parsed_url.hostname
                
                context = ssl.create_default_context()
                with socket.create_connection((hostname, 443), timeout=self.timeout) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
                        secure_sock.getpeercert()
                        result['ssl_valid'] = True
            except Exception:
                result['ssl_valid'] = False

        except Exception as e:
            error_mapping = {
                requests.exceptions.SSLError: ('SSL Error', 'SSL Certificate Verification Failed'),
                requests.exceptions.ConnectionError: ('Connection Error', 'Unable to connect to the server'),
                requests.exceptions.Timeout: ('Timeout', 'Request timed out')
            }
            
            error_type = type(e)
            result.update({
                'status': error_mapping.get(error_type, ('Error', str(e)))[0],
                'error': error_mapping.get(error_type, ('Error', str(e)))[1]
            })

        return result

    def batch_url_status_check(self, urls):
        """
        Perform batch URL status checks with advanced memory and performance management
        
        :param urls: List of URLs to check
        :return: DataFrame with URL status results
        """
        # Sample URLs if needed
        sampled_urls = self._sample_urls(urls)
        
        # Apply batch size limit if configured
        if self.batch_size:
            batched_urls = [sampled_urls[i:i + self.batch_size] for i in range(0, len(sampled_urls), self.batch_size)]
        else:
            batched_urls = [sampled_urls]

        all_results = []
        total_urls = len(sampled_urls)
        processed_urls = 0

        for batch in batched_urls:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Use generator to reduce memory overhead
                futures = {executor.submit(self._check_url_status, url): url for url in batch}
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    all_results.append(result)
                    
                    processed_urls += 1
                    st.progress(processed_urls / total_urls)

        return pd.DataFrame(all_results)

def main():
    st.set_page_config(page_title="SitemapSage Pro", page_icon="🌐", layout="wide")
    st.title("🌐 SitemapSage Pro: Advanced URL Status Checker")
    
    # Tabs for different input methods
    tab1, tab2 = st.tabs(["Manual URLs", "Sitemap Extraction"])
    
    with tab1:
        st.subheader("Manual URL Entry")
        
        # URL Input
        urls = st.text_area(
            "Enter URLs to check (one per line)", 
            placeholder="https://example.com\nhttps://another-example.com"
        )
        
        # Performance Options
        with st.sidebar:
            st.header("🛠️ Performance Configuration")
            timeout = st.slider("Request Timeout (seconds)", 5, 60, 10)
            max_workers = st.slider("Concurrent Workers", 1, 30, 10)
            
            # Sampling and Batch Processing
            sampling_rate = st.slider("URL Sampling Rate", 0.1, 1.0, 1.0, step=0.1,
                help="Process a percentage of URLs to manage large sets")
            
            batch_size = st.number_input(
                "Batch Size Limit", 
                min_value=0, 
                max_value=1000, 
                value=0,
                help="Limit number of URLs processed per batch (0 = no limit)"
            )
            
            # Optional Status Checking Toggle
            perform_detailed_check = st.checkbox(
                "Perform Detailed Status Check", 
                value=True,
                help="Uncheck to skip comprehensive URL analysis"
            )

        # Check URLs Button
        if st.button("🔍 Check URL Status (Manual)"):
            if urls and perform_detailed_check:
                url_list = [url.strip() for url in urls.split('\n') if url.strip()]
                
                # Progress and Performance Tracking
                with st.spinner('Analyzing URLs...'):
                    # Initialize checker with advanced configurations
                    checker = URLStatusChecker(
                        max_workers=max_workers, 
                        timeout=timeout,
                        sampling_rate=sampling_rate,
                        batch_size=batch_size if batch_size > 0 else None
                    )
                    
                    # Perform URL status check
                    results_df = checker.batch_url_status_check(url_list)
                
                # Results Visualization
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
                        file_name="url_status_results.csv",
                        mime="text/csv"
                    )
                with col2:
                    excel_buffer = BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        results_df.to_excel(writer, index=False)
                    st.download_button(
                        label="📊 Download Excel",
                        data=excel_buffer.getvalue(),
                        file_name="url_status_results.xlsx",
                        mime="application/vnd.ms-excel"
                    )
            else:
                st.warning("Please enter URLs to check or enable detailed status checking")
    
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
                        
                        # Results display (same as manual URL tab)
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
                            healthy_urls =
