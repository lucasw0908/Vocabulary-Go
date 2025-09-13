import $ from 'jquery';

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrf_token);
        }
    }
});

$("#deleteLibraryBtn").on("click", deleteLibrary);

function deleteLibrary(e) {
    e.preventDefault();
    const btn = e.currentTarget;
    const name = btn.getAttribute('data-name');
    if (!name) return;
    if (!confirm(`確定要刪除題庫「${name}」嗎？此動作無法復原。`)) return;
    $.ajax({
        url: `/api/library/${encodeURIComponent(name)}`,
        type: 'DELETE',
        success: function(result) {
            // On success, remove the row from the DOM
            const item = btn.closest('.list-group-item');
            if (item) item.remove();
            console.log(`題庫「${name}」已刪除。`);
        },
        error: function(xhr, status, error) {
            alert(`刪除題庫失敗: ${xhr.responseText || status}`);
        }
    })
}