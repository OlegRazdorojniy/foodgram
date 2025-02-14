import os
import shutil

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Initialize media directories and copy default files'

    def handle(self, *args, **options):
        avatar_dir = os.path.join(settings.MEDIA_ROOT, 'users/avatars')
        recipes_dir = os.path.join(settings.MEDIA_ROOT, 'recipes/images')

        os.makedirs(avatar_dir, exist_ok=True)
        os.makedirs(recipes_dir, exist_ok=True)

        default_avatar_src = os.path.join(
            settings.BASE_DIR,
            'users/static/users/default.png'
        )
        default_avatar_dest = os.path.join(
            settings.MEDIA_ROOT,
            settings.DEFAULT_USER_AVATAR
        )

        if not os.path.exists(default_avatar_dest):
            try:
                shutil.copy2(default_avatar_src, default_avatar_dest)
                self.stdout.write(
                    self.style.SUCCESS(
                        'Successfully copied default avatar'
                    )
                )
            except FileNotFoundError:
                self.stdout.write(
                    self.style.WARNING(
                        f'Default avatar not found at {default_avatar_src}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error copying default avatar: {e}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully initialized media directories')
        )
