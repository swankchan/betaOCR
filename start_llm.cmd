# 🎯 專為單人金融 OCR 深度優化的 C++ 視覺伺服器指令
# -ngl -1, all workload to GPU
# -np 1, no. of slots to be parallel run the task.  Be careful that in app.py "sem = asyncio.Semaphore(1)" set the frontend parallel wishes, but backend -np will be the bottleneck.  That's say sem should not larger than -np.
# -c is the context size , means tokens , say 65536, but -np 5, then 65536/5 = 13107 in each task
models\llama-cpp-vulkan\llama-server.exe -m models\Qwen3VL-8B-Instruct\Qwen3VL-8B-Instruct-Q4_K_M.gguf --mmproj models\Qwen3VL-8B-Instruct\mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf --port 8080 -c 65536 -ngl -1 -np 1 --image-min-tokens 1024