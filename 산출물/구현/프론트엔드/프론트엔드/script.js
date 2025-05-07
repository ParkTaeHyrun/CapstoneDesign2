document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const id = document.getElementById('userid').value;
    const pw = document.getElementById('password').value;
    alert(`아이디: ${id}\n비밀번호: ${pw}\n(실제 로그인 기능은 구현되어 있지 않습니다.)`);
}); 