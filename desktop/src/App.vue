<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { open } from "@tauri-apps/plugin-dialog";
import { invoke } from "@tauri-apps/api/core";
import { getVersion } from "@tauri-apps/api/app";
import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import { check } from "@tauri-apps/plugin-updater";
import { relaunch } from "@tauri-apps/plugin-process";

interface SelectedFile {
  name: string;
  size: number;
  path: string;
}

interface FileInfo {
  name: string;
  size: number;
}

interface TranscriptionEvent {
  type: string;
  file?: string;
  text?: string;
  message?: string;
  segment?: number;
  total_segments?: number;
  total_chunks?: number;
  progress?: number;
}

const selectedFile = ref<SelectedFile | null>(null);

const isTranscribing = ref(false);
const transcript = ref("");
const progress = ref(0);
const statusText = ref("Aguardando");
const errorMessage = ref("");

let unlistenTranscription: UnlistenFn | null = null;

// Atualizações do aplicativo.
const appVersion = ref("...");
const isCheckingUpdate = ref(false);
const isDownloadingUpdate = ref(false);
const updateAvailable = ref(false);
const updateVersion = ref("");
const updateProgress = ref(0);
const updateMessage = ref("");
const updateError = ref("");

let availableUpdate: Awaited<ReturnType<typeof check>> = null;

const formattedFileSize = computed(() => {
  if (!selectedFile.value) return "";

  const size = selectedFile.value.size;

  return size >= 1024 * 1024 * 1024
    ? `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`
    : size >= 1024 * 1024
      ? `${(size / (1024 * 1024)).toFixed(2)} MB`
      : `${(size / 1024).toFixed(2)} KB`;
});

// Consulta a versão instalada e verifica atualizações.
async function checkForUpdates() {
  if (isCheckingUpdate.value || isDownloadingUpdate.value) return;

  isCheckingUpdate.value = true;
  updateError.value = "";
  updateMessage.value = "";

  try {
    appVersion.value = await getVersion();

    const update = await check();

    if (update) {
      availableUpdate = update;
      updateAvailable.value = true;
      updateVersion.value = update.version;
      updateMessage.value = `A versão ${update.version} está disponível.`;
    } else {
      availableUpdate = null;
      updateAvailable.value = false;
      updateVersion.value = "";
      updateMessage.value = "Você está utilizando a versão mais recente.";
    }
  } catch (error) {
    console.error("Erro ao verificar atualizações:", error);
    updateError.value = "Não foi possível verificar atualizações.";
  } finally {
    isCheckingUpdate.value = false;
  }
}

// Baixa e instala a atualização disponível.
async function installUpdate() {
  if (!availableUpdate || isDownloadingUpdate.value) return;

  isDownloadingUpdate.value = true;
  updateProgress.value = 0;
  updateError.value = "";
  updateMessage.value = "Preparando atualização...";

  try {
    let downloadedBytes = 0;
    let contentLength = 0;

    await availableUpdate.downloadAndInstall((event) => {
      switch (event.event) {
        case "Started":
          contentLength = event.data.contentLength ?? 0;
          updateMessage.value = "Baixando atualização...";
          break;

        case "Progress":
          downloadedBytes += event.data.chunkLength;

          if (contentLength > 0) {
            updateProgress.value = Math.min(
              100,
              Math.round((downloadedBytes / contentLength) * 100),
            );
          }

          break;

        case "Finished":
          updateProgress.value = 100;
          updateMessage.value = "Instalando atualização...";
          break;
      }
    });

    updateMessage.value = "Atualização instalada. Reiniciando...";

    await relaunch();
  } catch (error) {
    console.error("Erro ao instalar atualização:", error);
    updateError.value = `Não foi possível instalar a atualização: ${String(error)}`;
    updateMessage.value = "";
  } finally {
    isDownloadingUpdate.value = false;
  }
}

// Abre o seletor nativo de arquivos do sistema.
async function openFileSelector() {
  if (isTranscribing.value) return;

  try {
    const selected = await open({
      multiple: false,
      directory: false,
      filters: [
        {
          name: "Arquivos de mídia",
          extensions: [
            "mp3",
            "mp4",
            "wav",
            "m4a",
            "mkv",
            "mov",
            "avi",
            "flac",
            "ogg",
            "webm",
          ],
        },
      ],
    });

    if (!selected || Array.isArray(selected)) return;

    const info = await invoke<FileInfo>("get_file_info", {
      filePath: selected,
    });

    selectedFile.value = {
      name: info.name,
      size: info.size,
      path: selected,
    };

    transcript.value = "";
    progress.value = 0;
    errorMessage.value = "";
    statusText.value = "Aguardando";
  } catch (error) {
    errorMessage.value = String(error);
  }
}

// Remove o arquivo selecionado.
function removeFile() {
  if (isTranscribing.value) return;

  selectedFile.value = null;
  transcript.value = "";
  progress.value = 0;
  errorMessage.value = "";
  statusText.value = "Aguardando";
}

// Recebe os eventos enviados pelo Python através do Rust.
function handleTranscriptionEvent(event: TranscriptionEvent) {
  switch (event.type) {
    case "transcription_started":
      statusText.value = "Iniciando transcrição";
      progress.value = 0;
      break;

    case "segment_started":
      statusText.value = `Processando segmento ${event.segment}/${event.total_segments}`;
      break;

    case "text_received":
      if (event.text) {
        transcript.value += event.text;
      }
      break;

    case "segment_completed":
      progress.value = event.progress ?? progress.value;
      break;

    case "transcription_completed":
      progress.value = 100;
      statusText.value = "Concluída";
      break;

    case "transcription_error":
      statusText.value = "Erro na transcrição";
      errorMessage.value = event.message ?? "Erro desconhecido.";
      break;
  }
}

// Inicia a transcrição.
async function startTranscription() {
  if (!selectedFile.value || isTranscribing.value) return;

  isTranscribing.value = true;
  transcript.value = "";
  progress.value = 0;
  errorMessage.value = "";
  statusText.value = "Preparando transcrição";

  try {
    unlistenTranscription = await listen<TranscriptionEvent>(
      "transcription-event",
      (event) => {
        handleTranscriptionEvent(event.payload);
      },
    );

    await invoke("start_transcription", {
      filePath: selectedFile.value.path,
    });
  } catch (error) {
    errorMessage.value = String(error);
    statusText.value = "Erro na transcrição";
  } finally {
    isTranscribing.value = false;

    unlistenTranscription?.();
    unlistenTranscription = null;
  }
}

// Verifica atualizações ao abrir o aplicativo.
onMounted(async () => {
  try {
    appVersion.value = await getVersion();
  } catch (error) {
    console.error("Não foi possível obter a versão:", error);
  }

  await checkForUpdates();
});

// Remove o listener quando o componente for desmontado.
onUnmounted(() => {
  unlistenTranscription?.();
});
</script>

<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-icon">CA</div>

        <div>
          <h1>Claude Audiência</h1>
          <span>Transcrição inteligente</span>
        </div>
      </div>

      <div class="sidebar-content">
        <span class="sidebar-label">WORKSPACE</span>

        <button class="nav-item active">
          <span class="nav-icon">▤</span>
          Nova audiência
        </button>

        <button class="nav-item" disabled>
          <span class="nav-icon">◷</span>
          Histórico
          <span class="coming-soon">Em breve</span>
        </button>

        <div class="sidebar-divider"></div>

        <span class="sidebar-label">FERRAMENTAS</span>

        <button class="nav-item" disabled>
          <span class="nav-icon">✦</span>
          Análise com Claude
        </button>
      </div>

      <div class="sidebar-footer">
        <div class="status-indicator"></div>

        <div>
          <strong>Processamento local</strong>
          <span>Ambiente preparado</span>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div>
          <span class="breadcrumb">Workspace /</span>
          <strong>Nova audiência</strong>
        </div>

        <div class="topbar-actions">
          <span class="version-badge">VERSÃO {{ appVersion }}</span>

          <button
            class="update-check-button"
            type="button"
            :disabled="isCheckingUpdate || isDownloadingUpdate"
            @click="checkForUpdates"
          >
            {{ isCheckingUpdate ? "Verificando..." : "Verificar atualizações" }}
          </button>
        </div>
      </header>

      <section class="workspace">
        <div class="page-heading">
          <div>
            <span class="eyebrow">TRANSCRIÇÃO DE AUDIÊNCIAS</span>

            <h2>Nova audiência</h2>

            <p>
              Selecione um arquivo para iniciar o processamento e gerar a
              transcrição.
            </p>
          </div>
        </div>
        <section
          v-if="updateAvailable || updateError || updateMessage"
          class="update-card"
        >
          <div class="update-card-content">
            <div class="update-card-icon">↻</div>

            <div class="update-card-information">
              <strong v-if="updateAvailable"> Nova versão disponível </strong>

              <strong v-else-if="updateError">
                Verificação de atualizações
              </strong>

              <strong v-else> Atualizações </strong>

              <p v-if="updateAvailable">
                A versão {{ updateVersion }} está disponível para instalação.
              </p>

              <p v-else-if="updateError">
                {{ updateError }}
              </p>

              <p v-else>
                {{ updateMessage }}
              </p>
            </div>

            <button
              v-if="updateAvailable && !isDownloadingUpdate"
              class="primary-button"
              type="button"
              @click="installUpdate"
            >
              Atualizar agora →
            </button>
          </div>

          <div v-if="isDownloadingUpdate" class="update-progress">
            <div class="progress-information">
              <span>{{ updateMessage }}</span>
              <strong>{{ updateProgress }}%</strong>
            </div>

            <div class="progress-track">
              <div
                class="progress-fill"
                :style="{ width: `${updateProgress}%` }"
              ></div>
            </div>
          </div>
        </section>

        <section class="upload-card">
          <div class="section-heading">
            <div>
              <h3>Arquivo de mídia</h3>
              <p>Selecione o áudio ou vídeo da audiência.</p>
            </div>

            <span class="step-number">01</span>
          </div>

          <div
            v-if="!selectedFile"
            class="upload-area"
            @click="openFileSelector"
          >
            <div class="upload-icon">
              <svg
                width="28"
                height="28"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M12 16V4" />
                <path d="m7 9 5-5 5 5" />
                <path
                  d="M20 16.5v2A1.5 1.5 0 0 1 18.5 20h-13A1.5 1.5 0 0 1 4 18.5v-2"
                />
              </svg>
            </div>

            <strong>Selecione seu arquivo</strong>

            <span> Clique para procurar um arquivo no computador. </span>

            <small> MP4, MKV, MOV, MP3, WAV, M4A e outros formatos. </small>

            <button class="secondary-button" type="button">
              Procurar arquivo
            </button>
          </div>

          <div v-else class="selected-file">
            <div class="file-icon">
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
              >
                <path
                  d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
                />
                <path d="M14 2v6h6" />
                <path d="M8 13h8M8 17h8" />
              </svg>
            </div>

            <div class="file-information">
              <strong>{{ selectedFile.name }}</strong>
              <span> {{ formattedFileSize }} · Arquivo selecionado </span>
            </div>

            <button
              class="remove-button"
              type="button"
              title="Remover arquivo"
              :disabled="isTranscribing"
              @click="removeFile"
            >
              ×
            </button>
          </div>

          <div class="upload-footer">
            <div class="local-processing">
              <span class="lock-icon">◆</span>
              Processamento de transcrição realizado localmente.
            </div>

            <button
              class="primary-button"
              type="button"
              :disabled="!selectedFile || isTranscribing"
              @click="startTranscription"
            >
              {{ isTranscribing ? "Transcrevendo..." : "Iniciar transcrição" }}
              <span>→</span>
            </button>
          </div>
        </section>

        <section class="transcript-card">
          <div class="section-heading">
            <div>
              <h3>Transcrição</h3>
              <p>O conteúdo processado aparecerá nesta área.</p>
            </div>

            <span
              class="waiting-badge"
              :class="{
                processing: isTranscribing,
                completed: progress === 100,
                failed: !!errorMessage,
              }"
            >
              <span></span>
              {{ statusText }}
            </span>
          </div>

          <textarea
            v-model="transcript"
            class="transcript-viewer"
            readonly
            placeholder="A transcrição aparecerá aqui conforme o processamento avançar..."
          ></textarea>

          <div v-if="isTranscribing || progress > 0" class="progress-container">
            <div class="progress-information">
              <span>{{ statusText }}</span>
              <strong>{{ progress }}%</strong>
            </div>

            <div class="progress-track">
              <div
                class="progress-fill"
                :style="{ width: `${progress}%` }"
              ></div>
            </div>
          </div>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>

          <div class="transcript-footer">
            <span>Somente leitura · Texto selecionável</span>

            <button class="secondary-button" type="button" disabled>
              Analisar audiência
              <span>✦</span>
            </button>
          </div>
        </section>
      </section>
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  background: #111318;
  color: #e7e8ec;
}

.sidebar {
  width: 250px;
  min-width: 250px;
  display: flex;
  flex-direction: column;
  background: #17191f;
  border-right: 1px solid #292c34;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 25px 20px;
  border-bottom: 1px solid #292c34;
}

.brand-icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  background: #c5a059;
  color: #17191f;
  font-size: 13px;
  font-weight: 800;
  border-radius: 9px;
}

.brand h1 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
}

.brand span {
  display: block;
  margin-top: 4px;
  color: #858995;
  font-size: 11px;
}

.sidebar-content {
  flex: 1;
  padding: 30px 14px;
}

.sidebar-label {
  display: block;
  margin: 0 10px 12px;
  color: #737782;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1.2px;
}

.nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 5px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #aeb1bb;
  text-align: left;
  font-size: 12px;
}

.nav-item.active {
  background: #292a30;
  color: #d8b36e;
}

.nav-item:disabled {
  opacity: 0.55;
}

.nav-icon {
  width: 18px;
  text-align: center;
  font-size: 16px;
}

.coming-soon {
  margin-left: auto;
  color: #777b85;
  font-size: 9px;
}

.sidebar-divider {
  height: 1px;
  margin: 25px 8px;
  background: #292c34;
}

.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #292c34;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #55b889;
  box-shadow: 0 0 10px #55b88955;
}

.sidebar-footer strong,
.sidebar-footer span {
  display: block;
  font-size: 11px;
}

.sidebar-footer span {
  margin-top: 4px;
  color: #777b85;
  font-size: 10px;
}

.main-content {
  flex: 1;
  min-width: 0;
}

.topbar {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 45px;
  border-bottom: 1px solid #292c34;
}

.topbar div:first-child {
  font-size: 12px;
}

.breadcrumb {
  margin-right: 8px;
  color: #777b85;
}

.version-badge {
  padding: 6px 10px;
  border: 1px solid #353945;
  border-radius: 4px;
  color: #aeb1bb;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1px;
}

.workspace {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: 55px 45px;
}

.page-heading {
  margin-bottom: 32px;
}

.eyebrow {
  color: #c5a059;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1.5px;
}

.page-heading h2 {
  margin: 12px 0 8px;
  font-size: 27px;
  font-weight: 650;
  letter-spacing: -0.8px;
}

.page-heading p,
.section-heading p {
  margin: 0;
  color: #858995;
  font-size: 12px;
}

.upload-card,
.transcript-card {
  padding: 25px;
  margin-bottom: 20px;
  border: 1px solid #292c34;
  border-radius: 9px;
  background: #191b22;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
}

.section-heading h3 {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 650;
}

.step-number {
  color: #777b85;
  font-size: 12px;
}

.upload-area {
  min-height: 235px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1px dashed #444854;
  border-radius: 7px;
  background: #15171d;
  cursor: pointer;
  transition:
    border-color 0.2s,
    background 0.2s;
}

.upload-area:hover {
  border-color: #c5a059;
  background: #1b1c21;
}

.upload-icon {
  margin-bottom: 15px;
  color: #c5a059;
}

.upload-area strong {
  margin-bottom: 7px;
  font-size: 13px;
}

.upload-area span,
.upload-area small {
  color: #858995;
  font-size: 11px;
}

.upload-area small {
  margin-top: 12px;
  font-size: 10px;
}

.secondary-button,
.primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s;
}

.secondary-button {
  border: 1px solid #3b3f49;
  background: #22252d;
  color: #d8d9df;
}

.upload-area .secondary-button {
  margin-top: 18px;
}

.secondary-button:not(:disabled):hover {
  border-color: #c5a059;
}

.primary-button {
  border: 1px solid #c5a059;
  background: #c5a059;
  color: #17191f;
}

.primary-button:not(:disabled):hover {
  background: #d4b16e;
}

.primary-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.upload-footer,
.transcript-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  margin-top: 22px;
}

.local-processing {
  color: #858995;
  font-size: 10px;
}

.lock-icon {
  margin-right: 6px;
  color: #55b889;
}

.selected-file {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  border: 1px solid #353945;
  border-radius: 7px;
  background: #15171d;
}

.file-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 7px;
  background: #302b21;
  color: #c5a059;
}

.file-information {
  flex: 1;
  min-width: 0;
}

.file-information strong {
  display: block;
  overflow: hidden;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-information span {
  display: block;
  margin-top: 5px;
  color: #858995;
  font-size: 10px;
}

.remove-button {
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 5px;
  background: transparent;
  color: #858995;
  font-size: 20px;
  cursor: pointer;
}

.remove-button:hover {
  background: #30252a;
  color: #e77979;
}

.remove-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.waiting-badge {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px;
  border-radius: 20px;
  background: #252830;
  color: #aeb1bb;
  font-size: 10px;
}

.waiting-badge span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #858995;
}

.waiting-badge.processing {
  color: #d8b36e;
}

.waiting-badge.processing span {
  background: #d8b36e;
  animation: pulse 1.2s infinite;
}

.waiting-badge.completed {
  color: #55b889;
}

.waiting-badge.completed span {
  background: #55b889;
}

.waiting-badge.failed {
  color: #e77979;
}

.waiting-badge.failed span {
  background: #e77979;
}

.transcript-viewer {
  width: 100%;
  min-height: 220px;
  padding: 18px;
  resize: vertical;
  border: 1px solid #30333d;
  border-radius: 6px;
  outline: none;
  background: #14161c;
  color: #d6d8df;
  font-family: inherit;
  font-size: 12px;
  line-height: 1.8;
}

.transcript-viewer::placeholder {
  color: #686d79;
}

.progress-container {
  margin-top: 18px;
}

.progress-information {
  display: flex;
  justify-content: space-between;
  margin-bottom: 9px;
  color: #aeb1bb;
  font-size: 10px;
}

.progress-information strong {
  color: #d8b36e;
}

.progress-track {
  height: 5px;
  overflow: hidden;
  border-radius: 10px;
  background: #30333d;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: #c5a059;
  transition: width 0.3s ease;
}

.error-message {
  margin-top: 15px;
  padding: 12px;
  border: 1px solid #633b40;
  border-radius: 5px;
  background: #302126;
  color: #e77979;
  font-size: 11px;
  line-height: 1.5;
}

.transcript-footer {
  margin-top: 15px;
}

.transcript-footer > span {
  color: #777b85;
  font-size: 10px;
}

@keyframes pulse {
  50% {
    opacity: 0.35;
  }
}

@media (max-width: 900px) {
  .sidebar {
    width: 210px;
    min-width: 210px;
  }

  .workspace {
    padding: 35px 25px;
  }

  .topbar {
    padding: 0 25px;
  }
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.update-check-button {
  padding: 7px 11px;
  border: 1px solid #3b3f49;
  border-radius: 5px;
  background: #22252d;
  color: #d8d9df;
  font-size: 10px;
  cursor: pointer;
  transition: 0.2s;
}

.update-check-button:hover:not(:disabled) {
  border-color: #c5a059;
  color: #d8b36e;
}

.update-check-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.update-card {
  padding: 18px 20px;
  margin-bottom: 20px;
  border: 1px solid #66532f;
  border-radius: 8px;
  background: #211f1a;
}

.update-card-content {
  display: flex;
  align-items: center;
  gap: 14px;
}

.update-card-icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 7px;
  background: #302b21;
  color: #d8b36e;
  font-size: 22px;
}

.update-card-information {
  flex: 1;
  min-width: 0;
}

.update-card-information strong {
  display: block;
  margin-bottom: 5px;
  color: #e7d2a5;
  font-size: 12px;
}

.update-card-information p {
  margin: 0;
  color: #aeb1bb;
  font-size: 11px;
  line-height: 1.5;
}

.update-progress {
  margin-top: 18px;
}
</style>
