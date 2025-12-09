from django.contrib.auth import get_user_model
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transcriptionAPI.settings')
django.setup()

User = get_user_model()
username = 'admin'
email = 'admin@example.com'
password = 'admin'

if User.objects.filter(username=username).exists():
    print(f"User {username} exists. Resetting password...")
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
else:
    print(f"Creating user {username}...")
    User.objects.create_superuser(username, email, password)

print("Superuser 'admin' with password 'admin' is ready.")
