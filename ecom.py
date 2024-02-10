import streamlit as st
import numpy as np
import plotly.express as px
import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')
import geopandas as gpd
from shapely.geometry import Point

st.set_page_config(page_title="eCOMMERCE", page_icon=":shopping_trolley:", layout="wide")

st.title(" :shopping_trolley: eCOMMERCE DASHBOARD ANALYTICS")
st.markdown('<style>div.block-container{padding-top:1rem;}</style>',unsafe_allow_html=True)



# Sidebar
st.sidebar.title("Filter Options")

# File Uploader in Sidebar
fl = st.sidebar.file_uploader(":file_folder: Upload a file", type=(["csv", "txt", "xlsx", "xls"]))

if fl is not None:
    filename = fl.name
    st.sidebar.write(filename)
    df = pd.read_csv(fl, encoding="ISO-8859-1")
else:
    # Load data from GitHub repository initially upon deployment
    url = 'https://raw.githubusercontent.com/velascogringo/eCOMMERCE_DASHBOARD_INTERACTIVE/main/ecommerce_data.csv'
    df = pd.read_csv(url, encoding="ISO-8859-1")

    # Show the file name in the sidebar
    st.sidebar.write("Loaded File: ecommerce_data.csv")

# Date Filters in Sidebar
df["order_date"] = pd.to_datetime(df["order_date"], infer_datetime_format=True, dayfirst=True, errors='coerce')

# Date Filters in Sidebar
startDate = pd.to_datetime(df["order_date"], format="%d-%m-%Y").min()
endDate = pd.to_datetime(df["order_date"], format="%d-%m-%Y").max()
date1 = pd.to_datetime(st.sidebar.date_input("Start Date", startDate))
date2 = pd.to_datetime(st.sidebar.date_input("End Date", endDate))


df = df[(df["order_date"] >= pd.to_datetime(date1)) & (df["order_date"] <= pd.to_datetime(date2))].copy()


# Create sidebar Region
region = st.sidebar.multiselect("Select Region", df['customer_region'].unique())
if not region:
    df2 = df.copy()
else:
    df2 = df[df["customer_region"].isin(region)]

# Create sidebar for State
state_options = sorted(df2['customer_state'].unique())  # Sort the states alphabetically
state = st.sidebar.multiselect("Select State", state_options)
if not state:
    df3 = df2.copy()
else:
    df3 = df2[df2["customer_state"].isin(state)]

# Create sidebar for City
city = st.sidebar.multiselect("Select City", sorted(df3['customer_city'].unique()))

#filter data based on Region, State and City
if not region and not state and not city:
    filtered_df = df
elif not state and not city:
    filtered_df = df[df['customer_region'].isin(region)]
elif not region and not city:
    filtered_df = df[df['customer_state'].isin(state)]
elif state and city:
    filtered_df = df3[df['customer_state'].isin(state) & df3['customer_city'].isin(city)]
elif region and city:
    filtered_df = df3[df['customer_region'].isin(region) & df3['customer_city'].isin(city)]
elif region and state:
    filtered_df = df3[df['customer_region'].isin(region) & df3['customer_state'].isin(state)]
elif city:
    filtered_df = df3[df3['customer_city'].isin(city)]
else:
    filtered_df = df3[df3['customer_region'].isin(region) & df3['customer_state'].isin(state) & df3['customer_city'].isin(city)]

###################TOP KPI YTD METRICS############################
    
# Apply date filter and sort in a single step
df_filtered = filtered_df[(filtered_df['order_date'] >= date1) & (filtered_df['order_date'] <= date2)]

# Year for calculating YTD (January 1st of date2's year)
year_start = pd.to_datetime(f"{date2.year}-01-01")

# Filter data from the first day of the maximum year to the maximum date in date2
df_current_year = df_filtered[(df_filtered['order_date'] >= year_start) & (df_filtered['order_date'] <= date2)]

# Calculate YTD values using cumsum for Sales, Profit, and Orders
df_current_year['YTD_Sales'] = df_current_year.groupby(df_current_year['order_date'].dt.to_period('M'))['sales_per_order'].transform(pd.Series.cumsum)
df_current_year['YTD_Profit'] = df_current_year.groupby(df_current_year['order_date'].dt.to_period('M'))['profit_per_order'].transform(pd.Series.cumsum)
df_current_year['YTD_Orders'] = df_current_year.groupby(df_current_year['order_date'].dt.to_period('M'))['order_quantity'].transform(pd.Series.cumsum)

# Extract total YTD values for the current year
total_ytd_sales = df_current_year['YTD_Sales'].iloc[-1] if not df_current_year.empty else float('nan')
total_ytd_profit = df_current_year['YTD_Profit'].iloc[-1] if not df_current_year.empty else float('nan')
total_ytd_orders = df_current_year['YTD_Orders'].iloc[-1] if not df_current_year.empty else float('nan')

# Organize YTD KPIs into three columns
left_column, middle_column, right_column = st.columns(3)

# Display YTD Sales in the left column
with left_column:
    st.subheader("YTD Sales:")
    st.subheader(f"US $ {total_ytd_sales:,.2f}")

# Display YTD Profit in the middle column
with middle_column:
    st.subheader("YTD Profit:")
    st.subheader(f"US $ {total_ytd_profit:,.2f}")

# Display YTD Orders in the right column
with right_column:
    st.subheader("YTD Orders:")
    st.subheader(f"{total_ytd_orders:,}")

# Create an expander for YTD KPIs
with st.expander("YTD KPIs Data", expanded=True):
  # Get the unique years from the date filter and sort them from latest to oldest
    filtered_years = sorted(df_filtered['order_date'].dt.year.unique(), reverse=True)

    # Create an empty list to store DataFrames for each year
    ytd_kpis_data_list = []

    # Iterate over each year and calculate YTD metrics
    for year in filtered_years:
        # Filter data for the current year
        df_year = df_filtered[df_filtered['order_date'].dt.year == year]

        # Calculate YTD metrics for the current year using vectorized operations
        df_year['YTD_Sales'] = df_year.groupby(df_year['order_date'].dt.to_period('M'))['sales_per_order'].transform(pd.Series.cumsum)
        df_year['YTD_Profit'] = df_year.groupby(df_year['order_date'].dt.to_period('M'))['profit_per_order'].transform(pd.Series.cumsum)
        df_year['YTD_Orders'] = df_year.groupby(df_year['order_date'].dt.to_period('M'))['order_quantity'].transform(pd.Series.cumsum)

        # Extract total YTD values directly
        ytd_sales = df_year['YTD_Sales'].iloc[-1]  # Get the last value for YTD_Sales
        ytd_profit = df_year['YTD_Profit'].iloc[-1]
        ytd_orders = df_year['YTD_Orders'].iloc[-1]

        # Create a DataFrame for the current year
        ytd_kpis_data_year = pd.DataFrame({
            'Year': [str(year)],
            'YTD / PYTD Sales': [ytd_sales],
            'YTD / PYTD Profit': [ytd_profit],
            'YTD / PYTD Orders': [ytd_orders]
        })

        # Append the DataFrame to the list
        ytd_kpis_data_list.append(ytd_kpis_data_year)

    # Concatenate all DataFrames into a single DataFrame
    ytd_kpis_data = pd.concat(ytd_kpis_data_list, ignore_index=True)

    # Display YTD KPIs
    center_aligned_css = "<style> table {margin-left: auto; margin-right: auto;} th, td {text-align: center !important;}</style>"
    st.write(center_aligned_css, unsafe_allow_html=True)
    st.table(ytd_kpis_data)

    # Download button for YTD KPIs DataFrame
    csv_ytd_kpis = ytd_kpis_data.to_csv(index=False).encode('utf-8')
    st.download_button("Download YTD KPIs Data", data=csv_ytd_kpis, file_name=f'YTD_KPIs_{filtered_years[0]}_{filtered_years[-1]}.csv', mime='text/csv',
                       help='Click here to download YTD KPIs data as a CSV file')

# Add a separator to distinguish between YTD KPIs and the rest of the content
st.markdown("---")

#Create sales visualization
category_df = filtered_df.groupby(by=['category_name'], as_index = False)['sales_per_order'].sum()

# Create layout columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("Sales per Product Category")
    fig = px.bar(category_df, x= 'category_name' , y= 'sales_per_order', text = ['${:,.2f}'.format(x) for x in category_df['sales_per_order']], 
                 template= 'seaborn')

    st.plotly_chart(fig,use_container_width=True, height = 200)

# With col2

with col2:
    st.subheader("Sales per Region")
    fig = px.pie(filtered_df, values = 'sales_per_order', names = 'customer_region', hole=0.5)
    fig.update_traces(text = filtered_df['customer_region'], textposition = 'inside')
    st.plotly_chart(fig, use_container_width = True)

cl1, cl2 = st.columns(2)

with cl1:
    with st.expander('Category_Viewdata'):
        # Format and display category_df
        formatted_category_df = category_df.style.format({'sales_per_order': '${:,.2f}'})
        st.write(formatted_category_df)
        
        # Download button for category_df
        csv_category = category_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Category Data", data=csv_category, file_name='Category.csv', mime='text/csv',
                   help='Click here to download data as a CSV file')

with cl2:
    with st.expander('Region_Viewdata'):
        # Group by and sum for 'sales_per_order' in filtered_df
        region = filtered_df.groupby(by='customer_region', as_index=False)['sales_per_order'].sum()

        # Format and display region DataFrame
        formatted_region_df = region.style.format({'sales_per_order': '${:,.2f}'})
        st.write(formatted_region_df)

# Download button for region DataFrame
csv_region = region.to_csv(index=False).encode('utf-8')
st.download_button("Download Region Data", data=csv_region, file_name='Region.csv', mime='text/csv',
                   help='Click here to download data as a CSV file')
        

filtered_df['month_year'] = filtered_df['order_date'].dt.to_period('M')
st.subheader('Time Series Analysis')

# Group by month_year and sum the sales_per_order
linechart = pd.DataFrame(filtered_df.groupby(filtered_df['month_year'].dt.strftime('%Y : %b'))['sales_per_order'].sum()).reset_index()

# Sort the DataFrame by month_year
linechart['month_year'] = pd.to_datetime(linechart['month_year'], format='%Y : %b')
linechart = linechart.sort_values('month_year')

# Create the line chart
fig2 = px.line(linechart, x='month_year', y='sales_per_order', labels={'Sales': 'Amount'}, height=500, width=1000, template='gridon')

# Format x-axis ticks to show only months
fig2.update_xaxes(
    tickmode='array',
    tickvals=linechart['month_year'],
    ticktext=linechart['month_year'].dt.strftime('%b %Y'),
    title_text='Month/Year'  # Update x-axis label
)
# Update y-axis label
fig2.update_yaxes(title_text='Total Sales')
st.plotly_chart(fig2, use_container_width=True)

#download timeseries data
with st.expander('TimeSeries_View Data:'):
    # Apply thousand separator to the DataFrame
    styled_linechart = linechart.style.format('{:,.2f}', subset=['sales_per_order'])
    
    # Display the styled DataFrame
    st.write(styled_linechart)
    
    # Download button for the styled DataFrame
    csv = linechart.to_csv(index=False).encode('utf-8')
    st.download_button('Download Data', data=csv, file_name='TimeSeries.csv', mime='text/csv')

    # Create layout columns for Top 10 and Bottom 10 products
top_products_column, bottom_products_column = st.columns(2)

# Top 10 Products
with top_products_column:
    st.subheader("Top 10 Products")
    
    # Group by product and sum for 'sales_per_order' in df_filtered
    top_products = df_filtered.groupby(by='product_name', as_index=False)['sales_per_order'].sum()
    
    # Sort by sales_per_order in descending order and get top 10
    top_products = top_products.sort_values(by='sales_per_order', ascending=False).head(10)
   
  # Create a horizontal bar chart for top products
    fig_top_products = px.bar(top_products, x='sales_per_order', y='product_name', 
                          text=top_products['sales_per_order'], template='seaborn', labels={'sales_per_order': 'Sales'},
                          category_orders={'product_name': top_products['product_name'].tolist()})

# Format values in the chart to 1 decimal place with '$' sign and 'k' format
    fig_top_products.update_traces(texttemplate='%{text:$,.3s}', textposition='inside')

# Round the sales values to 1 decimal place
    top_products['sales_per_order'] = top_products['sales_per_order'].round(1)

# Remove Y-axis label
    fig_top_products.update_yaxes(title_text='Product')

    st.plotly_chart(fig_top_products, use_container_width=True)


    
    # Expander for Top 10 Products Table
    with st.expander("Top 10 Products Data", expanded=False):
        # Format and display top10_products DataFrame 
        formatted_top10_products = top_products.style.format({'sales_per_order': '${:,.2f}'})
        st.write(formatted_top10_products)
    
    # Download button for top10_products
        csv_top10_products = top_products.to_csv(index=False).encode('utf-8')
        st.download_button("Download Top 10 Products Data", data=csv_top10_products, file_name='Top10Products.csv', mime='text/csv',
                       help='Click here to download data as a CSV file')


# Bottom 10 Products
with bottom_products_column:
    st.subheader("Bottom 10 Products")
    
    # Group by product and sum for 'sales_per_order' in df_filtered
    bottom_products = df_filtered.groupby(by='product_name', as_index=False)['sales_per_order'].sum()
    
    # Sort by sales_per_order in ascending order and get bottom 10
    bottom_products = bottom_products.sort_values(by='sales_per_order').head(10)
    
    # Create a horizontal bar chart for bottom products
    fig_bottom_products = px.bar(bottom_products, x='sales_per_order', y='product_name', orientation='h',
                                 text='sales_per_order', template='seaborn', labels={'sales_per_order': 'Sales'},
                          category_orders={'product_name': bottom_products['product_name'].tolist()})
    
    # Format values in the chart to 2 decimal places with '$' sign
    fig_bottom_products.update_traces(texttemplate='%{text:$,.2s}', textposition='inside')

    # Round the sales values to 1 decimal place
    bottom_products['sales_per_order'] = bottom_products['sales_per_order'].round(1)

        # Remove Y-axis label
    fig_bottom_products.update_yaxes(title_text='Product')

    st.plotly_chart(fig_bottom_products, use_container_width=True)

# Expander for Bottom 10 Products Table
    with st.expander("Bottom 10 Products Data", expanded=False):
    # Format and display bottom10_products DataFrame 
        formatted_bottom10_products = bottom_products.style.format({'sales_per_order': '${:,.2f}'})
        st.write(formatted_bottom10_products)
    
    # Download button for bottom10_products
        csv_bottom10_products = bottom_products.to_csv(index=False).encode('utf-8')
        st.download_button("Download Bottom 10 Products Data", data=csv_bottom10_products, file_name='Bottom10Products.csv', mime='text/csv',
                       help='Click here to download data as a CSV file')
        

# SALES MAP

# Create a DataFrame with unique total sales values for each state
unique_total_sales_per_state = filtered_df.groupby('customer_state')['sales_per_order'].sum().reset_index()

# Drop duplicates to ensure unique values for each state
unique_total_sales_per_state = unique_total_sales_per_state.drop_duplicates(subset='customer_state')

# Create a dictionary to map each state to its unique total sales value
state_to_total_sales_dict = dict(zip(unique_total_sales_per_state['customer_state'], unique_total_sales_per_state['sales_per_order']))

# Add a new column 'total_sales' to the DataFrame for hover text
filtered_df['total_sales'] = filtered_df['customer_state'].map(state_to_total_sales_dict)

# Create scatter_mapbox without hover
fig_sales_concentration_map_no_hover = px.scatter_mapbox(
    filtered_df,
    lat='latitude',
    lon='longitude',
    color='customer_region',
    size='sales_per_order',
    color_discrete_sequence=px.colors.qualitative.Set1,
    template='seaborn',
    mapbox_style="carto-positron",
    center={"lat": 37.7749, "lon": -97.5191},
    zoom=3.5,
    opacity=.8,
    size_max=15,
    hover_name="customer_state",
    text='total_sales',  # Display total sales directly on the map
    custom_data=['customer_state', 'total_sales'],  # Include custom data for later use
)

# Customize the layout
fig_sales_concentration_map_no_hover.update_geos(fitbounds="locations")
fig_sales_concentration_map_no_hover.update_layout(
    legend_title_text='Region',
    height=1100,
    width=1600,
)

# Set text color to black
fig_sales_concentration_map_no_hover.update_traces(textfont_color='black')

st.plotly_chart(fig_sales_concentration_map_no_hover, use_container_width=True)


# Customize the layout to adjust the text position
fig_sales_concentration_map_no_hover.update_layout(
    hoverlabel=dict(bgcolor="white",font_size=12)
)


# Create an expander for displaying total sales per state
with st.expander(""):
    st.write("Total Sales per State:")
    
    # Format the 'sales_per_order' column with 2 decimals and a dollar sign
    total_sales_per_state_formatted = unique_total_sales_per_state.copy()
    total_sales_per_state_formatted['sales_per_order'] = total_sales_per_state_formatted['sales_per_order'].map('${:,.2f}'.format)
    
    # Center-align the table
    st.markdown(
        "<style> table {margin-left: auto; margin-right: auto;} </style>",
        unsafe_allow_html=True
    )
    
    # Display the total sales per state DataFrame with state names and a centered table
    st.table(total_sales_per_state_formatted)
    
    # Add a download button for the total sales per state DataFrame
    csv_data = total_sales_per_state_formatted.to_csv(index=True).encode('utf-8')
    st.download_button(
        label="Download Total Sales per State",
        data=csv_data,
        file_name="total_sales_per_state.csv",
        key="download_total_sales_per_state"
    )

# Create an expander for displaying total sales per state
with st.expander(""):
    st.write("Total Sales per State:")
    
    # Format the 'sales_per_order' column with 2 decimals and a dollar sign
    total_sales_per_state_formatted = unique_total_sales_per_state.copy()
    total_sales_per_state_formatted['sales_per_order'] = total_sales_per_state_formatted['sales_per_order'].map('${:,.2f}'.format)
    
    # Center-align the table
    st.markdown(
        "<style> table {margin-left: auto; margin-right: auto;} </style>",
        unsafe_allow_html=True
    )
    
    # Display the total sales per state DataFrame with state names and a centered table
    st.table(total_sales_per_state_formatted)
    
    # Add a download button for the total sales per state DataFrame
    csv_data = total_sales_per_state_formatted.to_csv(index=True).encode('utf-8')
    st.download_button(
        label="Download Total Sales per State",
        data=csv_data,
        file_name="total_sales_per_state.csv",
        key="download_total_sales_per_state"
    )



