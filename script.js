async function loadProducts() {
  try {
    const res = await fetch('/.netlify/functions/products');
    const products = await res.json();

    if (!Array.isArray(products) || products.length === 0) {
      showError('Нет доступных товаров.');
      return;
    }

    renderProducts(products);
  } catch (e) {
    showError('Ошибка при загрузке товаров. Пожалуйста, попробуйте позже.');
  }
}

function renderProducts(products) {
  const productsContainer = document.getElementById('products-list');
  productsContainer.innerHTML = '';
  products.forEach(product => {
    const item = document.createElement('div');
    item.className = 'product-item';
    item.innerHTML = `
      <div class="product-title">${product.name}</div>
      <div class="product-price">${product.price} руб.</div>
      ${product.photo_url ? `<img src="${product.photo_url}" alt="${product.name}" />` : ''}
    `;
    productsContainer.appendChild(item);
  });
}

function showError(message) {
  const productsContainer = document.getElementById('products-list');
  productsContainer.innerHTML = `<div class="error">${message}</div>`;
}

window.addEventListener('DOMContentLoaded', loadProducts);