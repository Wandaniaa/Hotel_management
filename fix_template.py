import re

filepath = r'd:\django\hotel_management\hotel\templates\booking_list.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix == without spaces in Django template tags
content = content.replace("status_filter=='pending'", "status_filter == 'pending'")
content = content.replace("status_filter=='confirmed'", "status_filter == 'confirmed'")
content = content.replace("status_filter=='checked_in'", "status_filter == 'checked_in'")
content = content.replace("status_filter=='cancelled'", "status_filter == 'cancelled'")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed!")
