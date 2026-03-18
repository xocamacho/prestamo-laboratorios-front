function toggleSidebar() { 
  document.getElementById('sidebar').classList.toggle('collapsed'); 
}
function toggleMenu(item) {
  const isOpen = item.classList.contains('open');
  document.querySelectorAll('.nav-item.open').forEach(el => el.classList.remove('open'));
  if (!isOpen) item.classList.add('open');
}