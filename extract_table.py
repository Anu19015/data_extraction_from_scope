import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup

st.title('HTML Table Extractor')

uploaded_file = st.file_uploader('Upload an HTML file', type=['html'])

def get_table_preview(table, max_rows=1):
    headers = [th.get_text(strip=True) for th in table.find_all('th')]
    rows = []
    for tr in table.find_all('tr')[1:]:
        cells = tr.find_all(['td', 'th'])
        row = [cell.get_text(strip=True) for cell in cells]
        if row:
            rows.append(row)
        if len(rows) >= max_rows:
            break
    if headers and all(len(row) == len(headers) for row in rows):
        df = pd.DataFrame(rows, columns=headers)
    else:
        df = pd.DataFrame(rows)
    return df.to_string(index=False, header=True) if not df.empty else '(empty)'

if uploaded_file is not None:
    html_content = uploaded_file.read().decode('utf-8')
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    st.write(f'Number of <table> tags found: {len(tables)}')
    if tables:
        # Build options for selectbox with only table titles
        table_titles = [f"Table {i}" for i in range(len(tables))]
        table_idx = st.sidebar.selectbox('Select a table to extract', range(len(tables)), format_func=lambda i: table_titles[i])
        table = tables[table_idx]

        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        rows = []
        for tr in table.find_all('tr')[1:]:
            cells = tr.find_all(['td', 'th'])
            row = [cell.get_text(strip=True) for cell in cells]
            if row:
                rows.append(row)
        if headers and all(len(row) == len(headers) for row in rows):
            df = pd.DataFrame(rows, columns=headers)
        else:
            df = pd.DataFrame(rows)
        st.write('Extracted DataFrame:')
        st.dataframe(df)

        # --- Advanced Filtering UI ---
        st.markdown('---')
        st.sidebar.header('Column Roles')
        # Let user pick which columns are channel, parameter, and statistics
        col_options = list(df.columns)
        channel_col = st.sidebar.selectbox('Select Channel/Source Column', col_options, index=0 if col_options else None)
        param_col = st.sidebar.selectbox('Select Parameter/Meas Column', col_options, index=1 if len(col_options) > 1 else 0)
        # Automatically use all columns except channel and parameter as statistics columns
        stat_cols = [col for col in col_options if col not in [channel_col, param_col]]
        # Increase sidebar width for better usability
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] {
                min-width: 400px;
                max-width: 500px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        if channel_col and param_col and stat_cols:
            st.sidebar.header('Filter Table')
            channels = df[channel_col].dropna().unique().tolist()
            params = df[param_col].dropna().unique().tolist()
            selected_channels = st.sidebar.multiselect('Select Channels', channels)
            selected_params = st.sidebar.multiselect('Select Parameters', params)
            selected_stats = st.sidebar.multiselect('Select Statistics Columns to Display', stat_cols, default=stat_cols)

            # Only filter if user has made selections
            filtered = df.copy()
            if selected_channels:
                filtered = filtered[filtered[channel_col].isin(selected_channels)]
            if selected_params:
                filtered = filtered[filtered[param_col].isin(selected_params)]
            display_stats = selected_stats if selected_stats else stat_cols

            if not filtered.empty and selected_channels:
                result = filtered[[channel_col, param_col] + display_stats]
                for ch in filtered[channel_col].unique():
                    st.markdown(f'### {ch}')
                    sub = result[result[channel_col] == ch]
                    sub = sub.set_index(param_col)
                    sub = sub[display_stats]
                    st.dataframe(sub)
            elif not selected_channels:
                st.info('Please select at least one channel in the sidebar to view data.')
            else:
                st.warning('No data matches the selected filters.')
        else:
            st.info('To use advanced filtering, please select channel/source and parameter columns.')
    else:
        st.warning('No tables found in the HTML.')
else:
    st.info('Please upload an HTML file to begin.')
