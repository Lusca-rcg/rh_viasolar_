from flask import Flask, request, send_file, render_template_string
import PyPDF2
import os
import io
import zipfile

app = Flask(__name__)

# Função para dividir o PDF e retornar a página como arquivo para download
def dividir_pdf(input_pdf):
    files = []
    with open(input_pdf, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)

        for i in range(num_pages):
            pdf_writer = PyPDF2.PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[i])

            # Utilizando buffer para armazenar o PDF em memória
            output_pdf = io.BytesIO()
            pdf_writer.write(output_pdf)
            output_pdf.seek(0)

            # Nome do arquivo
            file_name = f"contra_cheque_pagina_{i + 1}.pdf"
            files.append((file_name, output_pdf))
    return files

# Página principal
@app.route('/')
def index():
    html_content = '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Dividir PDF</title>
    </head>
    <body>
        <h2>Upload de PDF para Divisão</h2>
        <form id="uploadForm" enctype="multipart/form-data" method="POST" action="/upload">
            <input type="file" name="pdf" accept=".pdf" required>
            <button type="submit">Enviar</button>
        </form>

        <div id="result"></div>

        <script>
            const form = document.getElementById("uploadForm");
            const resultDiv = document.getElementById("result");

            form.addEventListener("submit", async (e) => {
                e.preventDefault();
                const formData = new FormData(form);

                try {
                    const response = await fetch("/upload", {
                        method: "POST",
                        body: formData
                    });
                    const blob = await response.blob();
                    const downloadUrl = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = downloadUrl;
                    a.download = "pdf_dividido.zip";
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                } catch (error) {
                    resultDiv.innerHTML = `<p>Erro: ${error.message}</p>`;
                }
            });
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_content)

# Rota de upload e divisão
@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return "Arquivo não encontrado no formulário."
    
    file = request.files['pdf']
    if file and file.filename.endswith('.pdf'):
        # Salva o arquivo temporariamente
        temp_path = os.path.join('temp', file.filename)
        os.makedirs('temp', exist_ok=True)
        file.save(temp_path)

        # Divide o PDF e obtém os arquivos gerados
        pdf_files = dividir_pdf(temp_path)

        # Cria um arquivo zip na memória
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_name, file_data in pdf_files:
                zip_file.writestr(file_name, file_data.getvalue())

        # Limpar o buffer e preparar para download
        zip_buffer.seek(0)

        # Remove o arquivo temporário
        os.remove(temp_path)

        # Retorna o arquivo zip para download
        return send_file(zip_buffer, as_attachment=True, download_name="pdf_dividido.zip", mimetype='application/zip')

    return "Erro ao fazer o upload ou arquivo inválido."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))
    # Para produção, use o comando abaixo: 