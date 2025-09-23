import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Union
import io
import base64
import json
import re

class ImageViewer:
    """Component for displaying and generating visualizations from agent responses."""
    
    def __init__(self):
        """Initialize the image viewer component."""
        self.supported_chart_types = [
            'bar', 'line', 'scatter', 'pie', 'histogram', 
            'box', 'violin', 'heatmap', 'area', 'funnel'
        ]
    
    def display_chart(self, chart_data: Union[Dict[str, Any], go.Figure]):
        """
        Display a chart using Plotly.
        
        Args:
            chart_data: Chart data or Plotly figure object
        """
        try:
            if isinstance(chart_data, go.Figure):
                st.plotly_chart(chart_data, use_container_width=True)
            elif isinstance(chart_data, dict):
                # Create chart from data dictionary
                fig = self._create_plotly_chart(chart_data)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Could not create chart from provided data")
            else:
                st.error("Unsupported chart data format")
        except Exception as e:
            st.error(f"Error displaying chart: {str(e)}")
    
    def _create_plotly_chart(self, data: Dict[str, Any]) -> Optional[go.Figure]:
        """
        Create a Plotly chart from data dictionary.
        
        Args:
            data: Dictionary containing chart data and configuration
            
        Returns:
            Plotly figure object or None if creation fails
        """
        try:
            chart_type = data.get('type', 'bar').lower()
            df = pd.DataFrame(data.get('data', []))
            
            if df.empty:
                return None
            
            title = data.get('title', 'Chart')
            x_col = data.get('x_column', df.columns[0] if len(df.columns) > 0 else None)
            y_col = data.get('y_column', df.columns[1] if len(df.columns) > 1 else None)
            
            # Create chart based on type
            if chart_type == 'bar':
                fig = px.bar(df, x=x_col, y=y_col, title=title)
            elif chart_type == 'line':
                fig = px.line(df, x=x_col, y=y_col, title=title)
            elif chart_type == 'scatter':
                fig = px.scatter(df, x=x_col, y=y_col, title=title)
            elif chart_type == 'pie':
                fig = px.pie(df, values=y_col, names=x_col, title=title)
            elif chart_type == 'histogram':
                fig = px.histogram(df, x=x_col, title=title)
            elif chart_type == 'box':
                fig = px.box(df, x=x_col, y=y_col, title=title)
            elif chart_type == 'area':
                fig = px.area(df, x=x_col, y=y_col, title=title)
            else:
                # Default to bar chart
                fig = px.bar(df, x=x_col, y=y_col, title=title)
            
            # Apply styling
            fig.update_layout(
                template='plotly_white',
                height=500,
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            st.error(f"Error creating chart: {str(e)}")
            return None
    
    def create_chart_from_table_response(self, response_text: str) -> Optional[go.Figure]:
        """
        Extract tabular data from response text and create a chart.
        
        Args:
            response_text: Response text containing markdown table
            
        Returns:
            Plotly figure or None if no table found
        """
        try:
            # Extract markdown table from response
            table_data = self._extract_table_from_markdown(response_text)
            
            if not table_data:
                return None
            
            df = pd.DataFrame(table_data['rows'][1:], columns=table_data['rows'][0])
            
            # Try to identify numeric columns for visualization
            numeric_cols = []
            for col in df.columns:
                try:
                    # Try to convert to numeric
                    pd.to_numeric(df[col], errors='raise')
                    numeric_cols.append(col)
                except:
                    pass
            
            if len(numeric_cols) == 0:
                return None
            
            # Determine best chart type based on data
            if len(df.columns) >= 2:
                x_col = df.columns[0]  # First column as category
                y_col = numeric_cols[0]  # First numeric column as value
                
                # Convert numeric column to actual numbers
                df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                
                # Create appropriate chart
                if len(df) <= 20:  # Bar chart for smaller datasets
                    fig = px.bar(df, x=x_col, y=y_col, 
                               title=f"{y_col} by {x_col}")
                else:  # Line chart for larger datasets
                    fig = px.line(df, x=x_col, y=y_col, 
                                title=f"{y_col} over {x_col}")
                
                fig.update_layout(
                    template='plotly_white',
                    height=500,
                    xaxis_title=x_col,
                    yaxis_title=y_col
                )
                
                return fig
            
            return None
            
        except Exception as e:
            st.error(f"Error creating chart from table: {str(e)}")
            return None
    
    def _extract_table_from_markdown(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract table data from markdown formatted text.
        
        Args:
            text: Text containing markdown table
            
        Returns:
            Dictionary with table data or None if no table found
        """
        try:
            lines = text.split('\n')
            table_lines = []
            in_table = False
            
            for line in lines:
                line = line.strip()
                if '|' in line:
                    if '---' in line:
                        in_table = True
                        continue
                    elif in_table or (not in_table and '|' in line):
                        table_lines.append(line)
                        in_table = True
                elif in_table and line == '':
                    break
            
            if len(table_lines) < 2:
                return None
            
            # Parse table rows
            rows = []
            for line in table_lines:
                if '|' in line:
                    # Split by | and clean up
                    cells = [cell.strip() for cell in line.split('|')]
                    # Remove empty first and last elements if they exist
                    if cells and cells[0] == '':
                        cells = cells[1:]
                    if cells and cells[-1] == '':
                        cells = cells[:-1]
                    
                    if cells:
                        rows.append(cells)
            
            return {"rows": rows} if rows else None
            
        except Exception:
            return None
    
    def display_data_insights(self, df: pd.DataFrame):
        """
        Display data insights and statistics.
        
        Args:
            df: Pandas DataFrame to analyze
        """
        try:
            st.subheader("📊 Data Insights")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Rows", len(df))
            
            with col2:
                st.metric("Total Columns", len(df.columns))
            
            with col3:
                numeric_cols = df.select_dtypes(include=['number']).columns
                st.metric("Numeric Columns", len(numeric_cols))
            
            # Show data types
            with st.expander("📋 Column Information"):
                col_info = pd.DataFrame({
                    'Column': df.columns,
                    'Data Type': [str(dtype) for dtype in df.dtypes],
                    'Non-Null Count': [df[col].count() for col in df.columns],
                    'Null Count': [df[col].isnull().sum() for col in df.columns]
                })
                st.dataframe(col_info, use_container_width=True)
            
            # Show basic statistics for numeric columns
            if len(numeric_cols) > 0:
                with st.expander("📈 Numeric Statistics"):
                    st.dataframe(df[numeric_cols].describe(), use_container_width=True)
            
        except Exception as e:
            st.error(f"Error displaying data insights: {str(e)}")
    
    def create_custom_chart(self, df: pd.DataFrame):
        """
        Allow user to create custom charts from the data.
        
        Args:
            df: Pandas DataFrame to visualize
        """
        try:
            st.subheader("🎨 Create Custom Chart")
            
            col1, col2 = st.columns(2)
            
            with col1:
                chart_type = st.selectbox(
                    "Chart Type",
                    self.supported_chart_types,
                    key="custom_chart_type"
                )
                
                x_column = st.selectbox(
                    "X-axis Column",
                    df.columns.tolist(),
                    key="custom_x_column"
                )
            
            with col2:
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                y_column = st.selectbox(
                    "Y-axis Column",
                    numeric_cols if numeric_cols else df.columns.tolist(),
                    key="custom_y_column"
                )
                
                title = st.text_input(
                    "Chart Title",
                    value=f"{y_column} by {x_column}",
                    key="custom_chart_title"
                )
            
            if st.button("Create Chart", key="create_custom_chart"):
                chart_data = {
                    'type': chart_type,
                    'data': df.to_dict('records'),
                    'x_column': x_column,
                    'y_column': y_column,
                    'title': title
                }
                
                fig = self._create_plotly_chart(chart_data)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Could not create chart with selected parameters")
        
        except Exception as e:
            st.error(f"Error creating custom chart: {str(e)}")
    
    def display_image_from_base64(self, base64_data: str, caption: str = ""):
        """
        Display an image from base64 encoded data.
        
        Args:
            base64_data: Base64 encoded image data
            caption: Optional caption for the image
        """
        try:
            st.image(
                io.BytesIO(base64.b64decode(base64_data)),
                caption=caption,
                use_column_width=True
            )
        except Exception as e:
            st.error(f"Error displaying image: {str(e)}")
    
    def export_chart_as_image(self, fig: go.Figure, filename: str = "chart"):
        """
        Export a Plotly chart as an image.
        
        Args:
            fig: Plotly figure to export
            filename: Filename for the exported image
        """
        try:
            # Export as PNG
            img_bytes = fig.to_image(format="png", width=800, height=600)
            
            # Create download button
            st.download_button(
                label="📥 Download Chart as PNG",
                data=img_bytes,
                file_name=f"{filename}.png",
                mime="image/png"
            )
        except Exception as e:
            st.error(f"Error exporting chart: {str(e)}")
    
    def create_dashboard_view(self, response_data: Dict[str, Any]):
        """
        Create a dashboard view with multiple visualizations.
        
        Args:
            response_data: Response data from the agent
        """
        try:
            st.subheader("📊 Dashboard View")
            
            # Extract table data if available
            response_text = response_data.get("response_text", "")
            table_data = self._extract_table_from_markdown(response_text)
            
            if table_data and len(table_data['rows']) > 1:
                df = pd.DataFrame(table_data['rows'][1:], columns=table_data['rows'][0])
                
                # Convert numeric columns
                for col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                    except:
                        pass
                
                # Create multiple views
                tab1, tab2, tab3 = st.tabs(["📈 Charts", "📋 Data", "🔍 Insights"])
                
                with tab1:
                    # Auto-generate chart
                    chart_fig = self.create_chart_from_table_response(response_text)
                    if chart_fig:
                        st.plotly_chart(chart_fig, use_container_width=True)
                        self.export_chart_as_image(chart_fig, "dashboard_chart")
                    
                    # Custom chart creator
                    self.create_custom_chart(df)
                
                with tab2:
                    st.dataframe(df, use_container_width=True)
                    
                    # Download data
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Data as CSV",
                        data=csv,
                        file_name="data.csv",
                        mime="text/csv"
                    )
                
                with tab3:
                    self.display_data_insights(df)
            
            else:
                st.info("No tabular data found in the response for visualization.")
        
        except Exception as e:
            st.error(f"Error creating dashboard view: {str(e)}")