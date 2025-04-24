from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class TopPageTests(TestCase):
    def setUp(self):
        # テスト用のユーザーを作成
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_top_page_status_code(self):
        """トップページが正常に表示されるか確認"""
        response = self.client.get(reverse('top'))
        self.assertEqual(response.status_code, 200)

    def test_top_page_template_used(self):
        """正しいテンプレートが使用されているか確認"""
        response = self.client.get(reverse('top'))
        self.assertTemplateUsed(response, 'attendance/top.html')

    def test_top_page_context(self):
        """コンテキストデータが正しく渡されているか確認"""
        response = self.client.get(reverse('top'))
        self.assertIn('weather_info', response.context)

    def test_weather_info_in_context(self):
        """天気情報がコンテキストに含まれているか確認"""
        response = self.client.get(reverse('top'))
        weather_info = response.context['weather_info']
        self.assertIn('today', weather_info)
        self.assertIn('icon_url', weather_info['today'])
        self.assertIn('temperature', weather_info['today'])

    def test_authenticated_user_access(self):
        """認証済みユーザーがアクセスできるか確認"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('top'))
        self.assertEqual(response.status_code, 200)

    def test_logout_redirect(self):
        """ログアウト後にトップページにリダイレクトされるか確認"""
        response = self.client.get(reverse('logout_to_top'), follow=True)
        self.assertRedirects(response, reverse('top'))