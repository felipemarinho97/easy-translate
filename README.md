# Easy Translate

Easy Translate is a tool to translate subtitles using AI models. This repo contains a server that is compatible with EasyNMT API and can be used as a drop-in replacement for EasyNMT.

## Supported Providers

For now, the server supports the following providers:
- OpenAI
- Amazon Bedrock

You can also use any OpenAI compatible server as a provider like an LiteLLM server.

# Configuring EasyNMT Server

Create a `.env` file inside the `easy-translate` directory. You can copy the `.env.example` file and rename it to `.env`.
Set the OpenAI API key and the model name in the `.env` file.

# Usage

Start the EasyNMT compatible server by running the following command:

```bash
docker-compose up -d
```

To translate a subtitle `.srt` file, you can use the following command:

```bash
python translate_srt.py input_file.srt output_file.srt 'zh-CN' 'pt-br' --server_url http://localhost:24080 --max_retries 1 --batch_size 100
```

This command will translate the input file from Chinese `zh-CN` to Brazilian Portuguese `pt-br` using the EasyNMT server running at `http://localhost:24080`. The translated subtitles will be saved to the output file.

## Batch Size

In the example above, the `--batch_size` is set to 100. This means that the script will send 100 lines of the subtitle file to the server for translation in each request.

Using a larger batch size can speed up the translation process. However, some models may return bad or incomplete translations when the batch size is too large. You can adjust the batch size using the `--batch_size` option. I recommend using a **maximum** batch of size `50` for less capable models like `gpt-4o-mini` and `100` for more capable models ones.

## Command Help

```
usage: translate_srt.py [-h] [--server_url SERVER_URL] [--batch_size BATCH_SIZE] [--max_retries MAX_RETRIES] [--retry_delay RETRY_DELAY] input_file output_file source_lang target_lang

Translate SRT subtitles using EasyNMT server

positional arguments:
  input_file            Path to the input .srt file
  output_file           Path to save the translated .srt file
  source_lang           Source language code (e.g., 'pt')
  target_lang           Target language code (e.g., 'en')

options:
  -h, --help            show this help message and exit
  --server_url SERVER_URL
                        EasyNMT server URL
  --batch_size BATCH_SIZE
                        Number of lines to send per translation request
  --max_retries MAX_RETRIES
                        Number of retries in case of server failure
  --retry_delay RETRY_DELAY
                        Delay (in seconds) between retries
```