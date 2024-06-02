document.getElementById('upload-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData();
    const fileInput = document.getElementById('file-input');
    const uploadButton = event.target.querySelector('button');
    const loadingDiv = document.getElementById('loading');
    const resultDiv = document.getElementById('result');
    const outputPre = document.getElementById('output');
    const downloadLink = document.getElementById('download-link');

    if (fileInput.files.length === 0) {
        alert('请选择一个文件!');
        return;
    }

    formData.append('file', fileInput.files[0]);

    // 禁用表单并显示加载提示和进度条
    fileInput.disabled = true;
    uploadButton.disabled = true;
    loadingDiv.style.display = 'block';
    resultDiv.style.display = 'none';
    downloadLink.style.display = 'none';

    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();

    // 恢复表单并隐藏加载提示和进度条
    fileInput.disabled = false;
    uploadButton.disabled = false;
    loadingDiv.style.display = 'none';

    if (result.error) {
        alert(result.error);
    } else {
        outputPre.textContent = result.text.join('\n');
        resultDiv.style.display = 'block';
        downloadLink.href = result.download_url;
        downloadLink.style.display = 'block';
    }
});
