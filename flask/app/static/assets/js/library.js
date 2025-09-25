import $ from 'jquery';

$(function () {

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        }
    });

    let currentPage = 1;
    let itemsPerPage = 3;

    function setCookie(name, value, days) {
        const d = new Date();
        d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${d.toUTCString()};path=/`;
    }

    function getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let c of ca) {
        c = c.trim();
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length);
        }
        return null;
    }

    function renderList(page = 1, filteredItems = items) {
        const startIndex = (page - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const paginatedItems = filteredItems.slice(startIndex, endIndex);

        const listContainer = document.getElementById('listContainer');
        listContainer.innerHTML = '';

        paginatedItems.forEach(item => {

            const button = document.createElement('button');
            button.className = 'item';
            if (item.name === current_library) button.className = 'item item-selected';
            
            const isQuote = !item.description;
            const randomQuote = fallbackQuotes[Math.floor(Math.random() * fallbackQuotes.length)];
            
            const favoriteIcon = item.is_favorited ? '★' : '☆';
            const favoriteClass = item.is_favorited ? 'favorited' : '';
            const privacyIndicator = !item.is_public ? '<span class="privacy-badge private">(非公開)</span>' : '';
            
            button.innerHTML = `
              <div class="lib-header">
                <div class="lib-title">${item.name} <span class="lib-count">（${item.count} 題）</span> ${privacyIndicator}</div>
                <button class="favorite-btn ${favoriteClass}" data-library="${item.name}" title="${item.is_favorited ? '取消收藏' : '收藏'}">
                  ${favoriteIcon}
                  <span class="favorite-count">${item.favorite_count}</span>
                </button>
              </div>
              <div class="lib-desc">${isQuote ? `<i>${randomQuote}</i>` : item.description}</div>
              <div class="lib-meta">
                <span>Author: ${item.author}</span>
                <span>Created: ${item.created_at.split(' ')[0]}</span>
              </div>
            `;  

            button.addEventListener('click', () => {
                if (button.classList.contains('item-selected')) return; // 如果已經選中，則不執行任何操作
                document.querySelectorAll('.item').forEach(btn => {
                    btn.className = 'item';
                });
                button.className = 'item item-selected'; // 切換題庫
                let library_name = item.name;
                $.ajax({
                    url: `/api/change_user_library/${library_name}`,
                    type: 'PUT',
                    success: function(data) {
                        setCookie('s-correctCount', '', -1);
                        setCookie('s-wrongCount', '', -1);
                        setCookie('s-usedIndices', '', -1);
                        setCookie('correctCount', '', -1);
                        setCookie('wrongCount', '', -1);
                        setCookie('usedIndices', '', -1);
                        console.log(data);
                    },
                    error: function(xhr, status, error) {
                        console.error('Error changing library:', error);
                        console.error('Response:', xhr.responseText);
                    }
                })
            });
            listContainer.appendChild(button);
            
            // 添加收藏按鈕事件監聽器
            const favoriteBtn = button.querySelector('.favorite-btn');
            favoriteBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // 防止觸發父元素的點擊事件
                toggleFavorite(item.name, favoriteBtn, button);
            });
        });

        renderPagination(filteredItems);
    }

    function renderPagination(filteredItems = items) {
        const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
        const pagination = document.getElementById('pagination');
        pagination.innerHTML = '';

        for (let i = 1; i <= totalPages; i++) {
            const button = document.createElement('button');
            button.textContent = i;
            button.disabled = i === currentPage;
            button.addEventListener('click', () => {
                currentPage = i;
                renderList(currentPage, filteredItems);
            });
            pagination.appendChild(button);
        }
    }

    // Handle search
    document.getElementById('searchInput').addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const filteredItems = items.filter(item => {
            const name = item.name || '';
            const description = item.description || '';
            return name.toLowerCase().includes(query) || description.toLowerCase().includes(query);
        });
        
        currentPage = 1;
        renderList(currentPage, filteredItems);
    });

    // 收藏功能
    function toggleFavorite(libraryName, button, itemElement) {
        $.ajax({
            url: `/api/favorites/${libraryName}`,
            type: 'PUT',
            success: function(data) {
                // 更新按鈕狀態
                const isFavorited = button.classList.contains('favorited');
                if (isFavorited) {
                    button.classList.remove('favorited');
                    button.innerHTML = '☆ <span class="favorite-count">' + (parseInt(button.querySelector('.favorite-count').textContent) - 1) + '</span>';
                    button.title = '收藏';
                } else {
                    button.classList.add('favorited');
                    button.innerHTML = '★ <span class="favorite-count">' + (parseInt(button.querySelector('.favorite-count').textContent) + 1) + '</span>';
                    button.title = '取消收藏';
                }
                
                // 重新排序列表
                const currentItem = items.find(item => item.name === libraryName);
                if (currentItem) {
                    currentItem.is_favorited = !isFavorited;
                    currentItem.favorite_count = isFavorited ? currentItem.favorite_count - 1 : currentItem.favorite_count + 1;
                    items.sort((a, b) => (-a.is_favorited + b.is_favorited) || (-a.favorite_count + b.favorite_count));
                    renderList(currentPage);
                }
            },
            error: function(xhr, status, error) {
                if (xhr.status === 401) {
                    window.location.href = '/login';
                }
                console.error('Error toggling favorite:', error);
                console.error('Response:', xhr.responseText);
            },
        })
    }

    console.log('Current library:', current_library);
    console.log('Fallback quotes:', fallbackQuotes);
    console.log('Library items:', items);

    renderList();
});
