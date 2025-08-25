import streamlit as st
from db import Tags

# Page header
st.markdown("# 🏷️ Manage Tags")
st.markdown("Create and organize tags to categorize your documents.")

# Cache tags to avoid repeated database queries
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_tags():
    """Get all tags from database with caching"""
    tags_query = Tags.select()
    # Convert to a list of dictionaries to make it pickle-serializable
    return [{'id': tag.id, 'name': tag.name} for tag in tags_query]

def delete_tag(tag_id: int):
    """Delete tag and clear cache"""
    Tags.delete().where(Tags.id == tag_id).execute()
    # Clear the cache so the tag list updates
    get_all_tags.clear()

@st.dialog("Add tag")
def add_tag_dialog_open():
    tag = st.text_input("Tag")
    if tag:
        if st.button("Add", key="add-tag-dialog-button"):
            try:
                Tags.create(name=tag)
                # Clear cache to refresh the tag list
                get_all_tags.clear()
                st.success(f"Tag '{tag}' added successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add tag: {e}")

st.button("Add Tag", key="add-tag-main-button", on_click=add_tag_dialog_open)

# Use cached tags
tags = get_all_tags()

if len(tags):
    for tag in tags:
        with st.container(border=True):
            tag_name_col, empty_space_col, delete_button_col = st.columns(
                3,
                vertical_alignment="center"
            )
            with tag_name_col:
                st.write(tag['name'])
            with empty_space_col:
                pass
            with delete_button_col:
                if st.button("Delete", key=f"delete-tag-button-{tag['id']}"):
                    delete_tag(tag['id'])
                    st.rerun()
else:
    st.info("No tags created yet. Please create one!")