import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from io import BytesIO

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
                    last_modified.append(lastmod.text if lastmod is not None else None)
        
        return pd.DataFrame({'URL': urls, 'Last Modified': last_modified})
    
    except Exception as e:
        st.error(f"Error processing sitemap: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("XML Sitemap URL Extractor")
    
    # Input field for sitemap URL
    sitemap_url = st.text_input("Enter XML Sitemap URL:", 
                               placeholder="https://example.com/sitemap.xml")
    
    if st.button("Extract URLs"):
        if sitemap_url:
            with st.spinner("Extracting URLs..."):
                df = extract_urls_from_sitemap(sitemap_url)
                
                if not df.empty:
                    st.success(f"Found {len(df)} URLs!")
                    st.dataframe(df)
                    
                    # Export options
                    col1, col2 = st.columns(2)
                    
                    # CSV export
                    csv = df.to_csv(index=False).encode('utf-8')
                    col1.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="sitemap_urls.csv",
                        mime="text/csv"
                    )
                    
                    # Excel export
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='URLs')
                    excel_data = buffer.getvalue()
                    col2.download_button(
                        label="Download Excel",
                        data=excel_data,
                        file_name="sitemap_urls.xlsx",
                        mime="application/vnd.ms-excel"
                    )
        else:
            st.warning("Please enter a sitemap URL")

if __name__ == "__main__":
    main()
