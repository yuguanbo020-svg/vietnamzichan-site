import { supabase } from '/js/supabase-client.js';
import { renderAuthState } from '/js/community.js?v=auth-v1';
const messages = {"zh": {"signup": "注册", "login": "登录", "hint": "通过邮件中的链接完成验证，无需密码或验证码。", "name": "昵称", "email": "邮箱", "signupButton": "发送确认链接", "loginButton": "发送登录链接", "signupSent": "确认链接已发送，请查收邮件并点击链接完成注册。", "loginSent": "登录链接已发送，请查收邮件并点击链接登录。", "failed": "发送失败，请稍后重试。", "new": "还没有账号？", "existing": "已经有账号？"}, "vi": {"signup": "Đăng ký", "login": "Đăng nhập", "hint": "Xác thực bằng liên kết trong email, không cần mật khẩu hoặc mã xác minh.", "name": "Biệt danh", "email": "Email", "signupButton": "Gửi liên kết xác nhận", "loginButton": "Gửi liên kết đăng nhập", "signupSent": "Đã gửi liên kết xác nhận. Hãy mở email và nhấp vào liên kết để đăng ký.", "loginSent": "Đã gửi liên kết đăng nhập. Hãy mở email và nhấp vào liên kết để đăng nhập.", "failed": "Không thể gửi. Vui lòng thử lại sau.", "new": "Chưa có tài khoản?", "existing": "Đã có tài khoản?"}, "en": {"signup": "Sign up", "login": "Log in", "hint": "Use the link in your email. No password or verification code is needed.", "name": "Nickname", "email": "Email", "signupButton": "Send confirmation link", "loginButton": "Send login link", "signupSent": "Confirmation link sent. Open your email and click the link to complete signup.", "loginSent": "Login link sent. Open your email and click the link to log in.", "failed": "Unable to send. Please try again later.", "new": "No account yet?", "existing": "Already have an account?"}};
const main = document.querySelector('[data-auth-mode]');
const lang = main.dataset.authLang;
const mode = main.dataset.authMode;
const copy = messages[lang];
const form = document.getElementById('emailAuthForm');
const message = document.getElementById('authMessage');
const button = document.getElementById('sendLink');
renderAuthState('authState');
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  button.disabled = true;
  message.textContent = '';
  message.className = 'msg';
  try {
    const options = {
      shouldCreateUser: mode === 'signup',
      emailRedirectTo: window.location.origin + '/' + lang + '/community/',
    };
    if (mode === 'signup') {
      const nickname = document.getElementById('displayName').value.trim();
      if (!nickname) { document.getElementById('displayName').focus(); return; }
      options.data = { display_name: nickname };
    }
    const { error } = await supabase.auth.signInWithOtp({
      email: document.getElementById('email').value.trim(), options,
    });
    if (error) throw error;
    message.textContent = copy[mode + 'Sent'];
    message.className = 'msg ok';
  } catch (error) {
    message.textContent = copy.failed;
    message.className = 'msg err';
  } finally {
    button.disabled = false;
  }
});
