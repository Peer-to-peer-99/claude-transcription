use std::{
    io::{BufRead, BufReader, Read},
    path::PathBuf,
    process::{Command, Stdio},
    thread,
};

use serde::{Deserialize, Serialize};
use serde_json::Value;
use tauri::{
    path::BaseDirectory,
    AppHandle,
    Emitter,
    Manager,
};
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct FileInfo {
    name: String,
    size: u64,
}

#[tauri::command]
fn get_file_info(file_path: String) -> Result<FileInfo, String> {
    let path = PathBuf::from(&file_path);

    let metadata = std::fs::metadata(&path)
        .map_err(|error| {
            format!("Não foi possível acessar o arquivo: {error}")
        })?;

    let name = path
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("Arquivo selecionado")
        .to_string();

    Ok(FileInfo {
        name,
        size: metadata.len(),
    })
}

#[tauri::command]
async fn start_transcription(
    app: AppHandle,
    file_path: String,
) -> Result<(), String> {
    tauri::async_runtime::spawn_blocking(move || {
        execute_transcription(app, file_path)
    })
    .await
    .map_err(|error| error.to_string())?
}
fn execute_transcription(
    app: AppHandle,
    file_path: String,
) -> Result<(), String> {

    let project_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .map_err(|error| error.to_string())?;

    // Desenvolvimento: utiliza a .venv.
    // Produção: utiliza o executável incluído no instalador.

    #[cfg(target_os = "windows")]
    let python = if cfg!(debug_assertions) {
        project_root
            .join(".venv")
            .join("Scripts")
            .join("python.exe")
    } else {
        app.path()
            .resolve(
                "audiencia/audiencia.exe",
                BaseDirectory::Resource,
            )
            .map_err(|error| error.to_string())?
    };

    #[cfg(not(target_os = "windows"))]
    let python = if cfg!(debug_assertions) {
        project_root
            .join(".venv")
            .join("bin")
            .join("python")
    } else {
        app.path()
            .resolve(
                "audiencia/audiencia",
                BaseDirectory::Resource,
            )
            .map_err(|error| error.to_string())?
    };

    if !python.exists() {
        return Err(format!(
            "Executável de transcrição não encontrado: {}",
            python.display()
        ));
    }

    // Diretório persistente de dados do aplicativo.
    let app_data_dir = app.path()
        .app_data_dir()
        .map_err(|error| error.to_string())?;

    let transcriptions_dir = app_data_dir.join("transcriptions");
    let model_dir = app_data_dir.join("models");

    std::fs::create_dir_all(&transcriptions_dir)
        .map_err(|error| error.to_string())?;

    std::fs::create_dir_all(&model_dir)
        .map_err(|error| error.to_string())?;

    // Prepara a execução.
    let mut command = Command::new(&python);

    if cfg!(debug_assertions) {
        command
            .arg("-u")
            .arg("-m")
            .arg("transcriber.cli")
            .current_dir(&project_root)
            .env("PYTHONPATH", project_root.join("src"));
    }

    command
        .arg(&file_path)
        .arg("--json-events")
        .env(
            "CLAUDE_AUDIENCIA_TRANSCRIPTIONS_DIR",
            &transcriptions_dir,
        )
        .env(
            "CLAUDE_AUDIENCIA_MODEL_DIR",
            &model_dir,
        )
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    let mut child = command
        .spawn()
        .map_err(|error| {
            format!("Não foi possível iniciar a transcrição: {error}")
        })?;

    let stdout = child.stdout.take()
        .ok_or("Não foi possível capturar stdout")?;

    let stderr = child.stderr.take()
        .ok_or("Não foi possível capturar stderr")?;

    let stderr_thread = thread::spawn(move || {
        let mut output = String::new();
        let mut reader = BufReader::new(stderr);

        let _ = reader.read_to_string(&mut output);

        output
    });

    let reader = BufReader::new(stdout);

    for line in reader.lines() {
        let line = line.map_err(|error| error.to_string())?;

        if line.trim().is_empty() {
            continue;
        }

        match serde_json::from_str::<Value>(&line) {
            Ok(event) => {
                app.emit("transcription-event", event)
                    .map_err(|error| error.to_string())?;
            }

            Err(error) => {
                eprintln!(
                    "Evento JSON inválido: {error}. Conteúdo: {line}"
                );
            }
        }
    }

    let status = child.wait()
        .map_err(|error| error.to_string())?;

    let stderr_output = stderr_thread
        .join()
        .map_err(|_| "Falha ao capturar stderr do Python")?;

    if !status.success() {
        return Err(if stderr_output.trim().is_empty() {
            "O processo de transcrição terminou com erro.".to_string()
        } else {
            format!(
                "Erro durante a transcrição:\n{stderr_output}"
            )
        });
    }

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .invoke_handler(tauri::generate_handler![
            get_file_info,
            start_transcription
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}