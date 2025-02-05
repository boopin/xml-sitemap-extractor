import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from io import BytesIO
import concurrent.futures
import time

# Page config
st.set_page_config(
    page_title="SitemapSage",
    page_icon="🗺️",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .subheader {
        font-size: 1.2rem;
        color: #424242;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
    }
    .url-count {
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
    }
    .processing-status {
        margin: 10px 0;
        padding: 10px;
        border-radius: 5px;
    }
    .success {
        background-color: #E8F5E9;
        color: #2E7D32;
    }
    .error {
        background-color: #FFEBEE;
        color: #C62828;
    }
    </style>
    """, unsafe_allow_html=True)

def extract_urls_from_sitemap(sitemap_url):
    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        namespaces = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'xhtml': 'http://www.w3.org/1999/xhtml'
        }
        
        urls = []
        last_modified = []
        change_freq = []
        priority = []
        source_sitemap = []
        
        if 'sitemapindex' in root.tag:
            for sitemap in root.findall('.//ns:loc', namespaces):
                sub_df = extract_urls_from_sitemap(sitemap.text)
                if not sub_df.empty:
                    urls.extend(sub_df['URL'].tolist())
                    last_modified.extend(sub_df['Last Modified'].tolist())
                    change_freq.extend(sub_df['Change Frequency'].tolist())
                    priority.extend(sub_df['Priority'].tolist())
                    source_sitemap.extend([sitemap_url] * len(sub_df))
        else:
            for url in root.findall('.//ns:url', namespaces):
                loc = url.find('ns:loc', namespaces)
                if loc is not None:
                    urls.append(loc.text)
                    lastmod = url.find('ns:lastmod', namespaces)
                    changefreq = url.find('ns:changefreq', namespaces)
                    pri = url.find('ns:priority', namespaces)
                    
                    last_modified.append(lastmod.text if lastmod is not None else None)
                    change_freq.append(changefreq.text if changefreq is not None else None)
                    priority.append(pri.text if pri is not None else None)
                    source_sitemap.append(sitemap_url)
        
        return pd.DataFrame({
            'URL': urls,
            'Last Modified': last_modified,
            'Change Frequency': change_freq,
            'Priority': priority,
            'Source Sitemap': source_sitemap
        })
    
    except Exception as e:
        st.error(f"Error processing {sitemap_url}: {str(e)}")
        return pd.DataFrame()

def process_sitemap(url):
    start_time = time.time()
    df = extract_urls_from_sitemap(url)
    processing_time = time.time() - start_time
    return {
        'url': url,
        'df': df,
        'processing_time': processing_time,
        'success': not df.empty
    }

def main():
    st.markdown("<h1 class='main-header'>🗺️ SitemapSage</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subheader'>Batch Process Multiple XML Sitemaps</p>", unsafe_allow_html=True)
    
    # Input method selector
    input_method = st.radio(
        "Choose input method:",
        ["Single URL", "Multiple URLs", "Upload File"]
    )
    
    sitemap_urls = []
    
    if input_method == "Single URL":
        url = st.text_input("Enter XML Sitemap URL:", placeholder="https://example.com/sitemap.xml")
        if url:
            sitemap_urls = [url]
    
    elif input_method == "Multiple URLs":
        urls_text = st.text_area(
            "Enter multiple sitemap URLs (one per line):",
            placeholder="https://example1.com/sitemap.xml\nhttps://example2.com/sitemap.xml"
        )
        if urls_text:
            sitemap_urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
    
    else:  # Upload File
        uploaded_file = st.file_uploader("Upload a text file with sitemap URLs (one per line)", type=['txt'])
        if uploaded_file:
            content = uploaded_file.getvalue().decode()
            sitemap_urls = [url.strip() for url in content.split('\n') if url.strip()]
    
    # Process button
    if st.button("🔍 Process Sitemaps", use_container_width=True):
        if sitemap_urls:
            progress_bar = st.progress(0)
            status_container = st.empty()
            
            # Initialize results storage
            all_results = pd.DataFrame()
            total_urls = 0
            successful_sitemaps = 0
            failed_sitemaps = 0
            
            # Process sitemaps with concurrent execution
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(process_sitemap, url): url for url in sitemap_urls}
                
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    result = future.result()
                    progress = (i + 1) / len(sitemap_urls)
                    progress_bar.progress(progress)
                    
                    if result['success']:
                        successful_sitemaps += 1
                        total_urls += len(result['df'])
                        all_results = pd.concat([all_results, result['df']], ignore_index=True)
                        status_text = f"✅ Processed {result['url']} ({len(result['df'])} URLs, {result['processing_time']:.2f}s)"
                    else:
                        failed_sitemaps += 1
                        status_text = f"❌ Failed to process {result['url']}"
                    
                    status_container.markdown(f"<div class='processing-status {'success' if result['success'] else 'error'}'>{status_text}</div>", unsafe_allow_html=True)
            
            # Display results
            if not all_results.empty:
                st.markdown(f"<p class='url-count'>📊 Processed {successful_sitemaps:,} sitemaps ({failed_sitemaps} failed)<br>Found {total_urls:,} unique URLs!</p>", unsafe_allow_html=True)
                
                # Show results grouped by sitemap
                st.subheader("Results by Sitemap")
                sitemap_stats = all_results.groupby('Source Sitemap').agg({
                    'URL': 'count',
                    'Last Modified': lambda x: x.notna().sum(),
                    'Priority': lambda x: x.notna().mean() * 100
                }).reset_index()
                sitemap_stats.columns = ['Sitemap', 'URLs Found', 'URLs with Last Modified', '% URLs with Priority']
                st.dataframe(sitemap_stats)
                
                # Show all URLs
                st.subheader("All URLs")
                st.dataframe(all_results, height=400)
                
                # Export options
                col1, col2 = st.columns(2)
                
                # CSV export
                csv = all_results.to_csv(index=False).encode('utf-8')
                col1.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="sitemap_urls.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                # Excel export
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    all_results.to_excel(writer, index=False, sheet_name='URLs')
                    sitemap_stats.to_excel(writer, index=False, sheet_name='Sitemap Stats')
                excel_data = buffer.getvalue()
                col2.download_button(
                    label="📊 Download Excel",
                    data=excel_data,
                    file_name="sitemap_urls.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True
                )
        else:
            st.warning("⚠️ Please provide at least one sitemap URL")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #666;'>Made with ❤️ by SitemapSage</p>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
