import streamlit as st
from helpers import free_seo_audit, ai_analysis, full_seo_audit, display_wrapped_json

def main():
    # Title and logo
    st.set_page_config(page_title="Bulk AI SEO Auditor", page_icon="🔍")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        st.markdown("# 🔍")  # Using markdown to display the emoji as text
    with col2:
        st.title("Bulk AI SEO Auditor 🚀")
    
    st.markdown("---")

    st.subheader("🛠️ Audit Configuration")
    audit_type = st.radio("Choose audit type:", ("✅ Simple Built-in Audit", "🔬 Full Local Audit"))

    uploaded_file = st.file_uploader("📂 Upload a text file containing URLs (one per line)", type="txt")

    if uploaded_file is not None:
        urls = uploaded_file.getvalue().decode("utf-8").splitlines()
        st.success(f"📊 Found {len(urls)} URLs in the uploaded file.")

        if st.button("🚀 Start Analysis"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, url in enumerate(urls):
                progress = (i + 1) / len(urls)
                progress_bar.progress(progress)
                status_text.text(f"🔍 Analyzing URL {i+1} of {len(urls)}: {url}")

                with st.expander(f"🌐 SEO Audit for {url}", expanded=False):
                    if "Simple" in audit_type:
                        report = free_seo_audit(url)
                    else:
                        report = full_seo_audit(url)

                    ai_result = ai_analysis(report)

                    ai_tab, seo_tab = st.tabs(["🤖 AI Analysis", "📊 SEO Report"])
                    with ai_tab:
                        st.subheader("🤖 AI Analysis")
                        st.write(ai_result)
                    with seo_tab:
                        st.subheader("📊 SEO Report")
                        display_wrapped_json(report)

            status_text.text("✅ Analysis complete!")
            progress_bar.progress(1.0)
    st.markdown("---")
    st.markdown("Made By Hamid Shah")

if __name__ == "__main__":
    main()