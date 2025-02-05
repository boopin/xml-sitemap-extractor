import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from io import BytesIO

# Page config for tab name and favicon
st.set_page_config(
    page_title="SitemapSage",
    page_icon="🗺️",
    layout="wide"
)

# Custom CSS for styling
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
    </style>
    """, unsafe_allow_html=True)

def extract_urls_from_sitemap(sitemap_url):
    try:
        # Fetch the sitemap
        response = requests.get(sitemap_url)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        # Handle different sitemap namespaces
        namespaces = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'xhtml': 'http://www.w3.org/1999/xhtml'
        }
        
        # Extract URLs
        urls = []
        last_modified = []
        change_freq = []
        priority = []
        
        # Check if it's a sitemap index
        if 'sitemapindex' in root.tag:
            for sitemap in root.findall('.//ns:loc', namespaces):
                sub_urls = extract_urls_from_sitemap(sitemap.text)
                urls.extend(sub_urls)
        else:
            # Regular sitemap
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
        
        return pd.DataFrame({
            'URL': urls,
            'Last Modified': last_modified,
            'Change Frequency': change_freq,
            'Priority': priority
        })
    
    except Exception as e:
        st.error(f"Error processing sitemap: {str(e)}")
        return pd.DataFrame()

def main():
    # Header
    st.markdown("<h1 class='main-header'>🗺️ SitemapSage</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subheader'>Extract, analyze, and export URLs from any XML sitemap</p>", unsafe_allow_html=True)
    
    # Create three columns for better layout
    left_col, main_col, right_col = st.columns([1, 2, 1])
    
    with main_col:
        # Input field with example
        sitemap_url = st.text_input(
            "Enter XML Sitemap URL:",
            placeholder="https://example.com/sitemap.xml"
        )
        
        # Process button
        if st.button("🔍 Extract URLs", use_container_width=True):
            if sitemap_url:
                with st.spinner("🔄 Processing sitemap..."):
                    df = extract_urls_from_sitemap(sitemap_url)
                    
                    if not df.empty:
                        st.markdown(f"<p class='url-count'>📊 Found {len(df):,} URLs!</p>", unsafe_allow_html=True)
                        
                        # Show dataframe with styling
                        st.dataframe(
                            df.style.highlight_null(null_color='#ffecb3'),
                            height=400
                        )
                        
                        # Export options in columns
                        col1, col2 = st.columns(2)
                        
                        # CSV export
                        csv = df.to_csv(index=False).encode('utf-8')
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
                            df.to_excel(writer, index=False, sheet_name='URLs')
                        excel_data = buffer.getvalue()
                        col2.download_button(
                            label="📊 Download Excel",
                            data=excel_data,
                            file_name="sitemap_urls.xlsx",
                            mime="application/vnd.ms-excel",
                            use_container_width=True
                        )
            else:
                st.warning("⚠️ Please enter a sitemap URL")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #666;'>Made with ❤️ by SitemapSage</p>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
