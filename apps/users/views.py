# _*_ coding _*_
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.views.generic.base import View
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.hashers import make_password

from .models import UserProfile, EmailVerifyRecord
from .forms import LoginForm, RegisterForm, ForgetForm, ModifyPwdForm
from utils.email_send import send_register_email
from utils.mixin_utils import LoginRequiredMixin

class CustomBackend(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        try:
            user = UserProfile.objects.get(Q(username=username) | Q(email=username))
            if user.check_password(password):
                return user
        except Exception as e:
            return None



# 用户注册
class RegisterView(View):
    def get(self, request):
        register_form = RegisterForm()
        return render(request, 'register.html', {'register_form': register_form})

    def post(self, request):
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            user_name = request.POST.get('email', '')
            if UserProfile.objects.filter(email=user_name):
                return render(request, 'register.html', {"register_form": register_form, "msg": "用户已经存在"})
            pass_word = request.POST.get('password', '')
            user_profile = UserProfile()
            user_profile.username = user_name
            user_profile.email = user_name
            user_profile.is_active = False
            user_profile.password = make_password(pass_word)
            user_profile.save()

            send_register_email(user_name, "register")
            return render(request, 'login.html')
        else:
            return render(request, 'register.html', {"register_form": register_form})

# 用户登录
class LoginView(View):
    def get(self, request):
        return render(request, 'login.html', {})

    def post(self, request):
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user_name = request.POST.get('username', '')
            password = request.POST.get('password', '')
            # 上面的 authenticate 方法 return user
            user = authenticate(username=user_name, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponsePermanentRedirect(reverse('index'))
                else:
                    return render(request, 'login.html', {'msg': '用户未激活！'})
            else:
                return render(request, 'login.html', {'msg': '用户名或者密码错误！'})
        else:
            return render(request, 'login.html', {'form_errors': login_form.errors})


# 验证用户注册后，在邮件里点击注册链接
class ActiveUserView(View):
    def get(self, request, active_code):
        # 为什么用 filter ？ 因为用户可能注册了好多次，一个 email 对应了好多个 code
        all_records = EmailVerifyRecord.objects.filter(code=active_code)
        if all_records:
            for records in all_records:
                email = records.email
                user = UserProfile.objects.get(email=email)
                user.is_active = True
                user.save()
                return render(request, 'login.html')
        else:
            return render(request, 'active_fail.html')

        return render(request, 'login.html')

# 忘记密码页面
class ForgetPwdView(View):
    def get(self, request):
        forget_form = ForgetForm()
        return render(request, 'forgetpwd.html', {'forget_form': forget_form})

    def post(self, request):
        forget_form = ForgetForm(request.POST)
        if forget_form.is_valid():
            email = request.POST.get('email', '')
            send_register_email(email, 'forget')
            return render(request, 'send_success.html')
        else:
            return render(request, 'forgetpwd.html', {'forget_form': forget_form})


# 用户进入到重置密码页面
class ResetView(View):
    def get(self, request, active_code):
        # 如果第二次进来，链接就失效
        all_records = EmailVerifyRecord.objects.filter(code=active_code)
        if all_records:
            for records in all_records:
                email = records.email
                return render(request, 'password_reset.html', {'email': email})
        return render(request, 'active_fail.html')


# 用户在重置密码页面提交新密码
class ModifyPwdView(View):
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        email = request.POST.get('email', '')
        if modify_form.is_valid():
            pwd1 = request.POST.get('password1', '')
            pwd2 = request.POST.get('password2', '')
            if pwd1 != pwd2:
                return render(request, 'password_reset.html', {'email': email, 'msg': '密码不一致！'})
            user = UserProfile.objects.get(email=email)
            user.password = make_password(pwd2)
            user.save()

            return render(request, 'login.html')
        else:
            return render(request, 'password_reset.html', {'email': email, 'modify_form': modify_form})


# 用户登出
class LogoutView(View):
    def get(self, request):
        logout(request)
        return HttpResponsePermanentRedirect(reverse('index'))


# 用户个人信息
class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'usercenter-info.html', {

        })