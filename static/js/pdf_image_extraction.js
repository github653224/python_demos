$(document).ready(function() {
    $('#upload-form').on('submit', function(e) {
        e.preventDefault();
        var formData = new FormData(this);

        $('#loading').show();
        $('#images').hide();
        $('#image-list').empty();
        $('#download-images-link').hide();

        $.ajax({
            url: '/upload', // 你的后端处理上传的URL
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function(response) {
                $('#loading').hide();
                if (response.images && response.images.length > 0) {
                    $('#images').show();
                    response.images.forEach(function(image) {
                        var img = $('<img>').attr('src', image).addClass('img-thumbnail m-2');
                        $('#image-list').append(img);
                    });
                    $('#download-images-link').show().attr('href', response.download_link);
                } else {
                    alert('未提取到任何图片');
                }
            },
            error: function() {
                $('#loading').hide();
                alert('上传失败，请重试');
            }
        });
    });
});
