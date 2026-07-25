'use client';

import { Camera, CircleDot, Mic, Square } from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

export interface WebcamAudioRecorderProps {
  onCaptureComplete: (audioBase64: string, videoFramesBase64: string[]) => void;
  snapshotIntervalMs?: number;
  className?: string;
  title?: string;
}

const DEFAULT_SNAPSHOT_INTERVAL_MS = 2000;

function formatDuration(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function pickSupportedAudioMimeType(): string {
  const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'];
  if (typeof MediaRecorder === 'undefined') return '';
  return candidates.find((type) => MediaRecorder.isTypeSupported(type)) ?? '';
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(reader.error ?? new Error('Impossible de lire le blob audio'));
    reader.onloadend = () => {
      const result = reader.result;
      if (typeof result !== 'string') {
        reject(new Error('Résultat de lecture invalide'));
        return;
      }
      const commaIndex = result.indexOf(',');
      resolve(commaIndex >= 0 ? result.slice(commaIndex + 1) : result);
    };
    reader.readAsDataURL(blob);
  });
}

export function WebcamAudioRecorder({
  onCaptureComplete,
  snapshotIntervalMs = DEFAULT_SNAPSHOT_INTERVAL_MS,
  className,
  title = 'Entretien webcam & audio',
}: WebcamAudioRecorderProps) {
  const [isInitializing, setIsInitializing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [capturedFrameCount, setCapturedFrameCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const audioMimeTypeRef = useRef<string>('');
  const audioChunksRef = useRef<Blob[]>([]);
  const videoFramesRef = useRef<string[]>([]);
  const elapsedTimerRef = useRef<number | null>(null);
  const snapshotTimerRef = useRef<number | null>(null);
  const emitResultRef = useRef(false);

  const formattedTime = useMemo(() => formatDuration(elapsedSeconds), [elapsedSeconds]);

  const clearTimers = useCallback(() => {
    if (elapsedTimerRef.current !== null) {
      window.clearInterval(elapsedTimerRef.current);
      elapsedTimerRef.current = null;
    }
    if (snapshotTimerRef.current !== null) {
      window.clearInterval(snapshotTimerRef.current);
      snapshotTimerRef.current = null;
    }
  }, []);

  const detachStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  const captureFrame = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    if (video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA || video.videoWidth === 0 || video.videoHeight === 0) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    if (!context) return;

    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    const base64 = dataUrl.includes(',') ? dataUrl.split(',', 2)[1] : dataUrl;
    if (base64) {
      videoFramesRef.current.push(base64);
      setCapturedFrameCount(videoFramesRef.current.length);
    }
  }, []);

  const finalizeCapture = useCallback(async () => {
    const chunks = audioChunksRef.current.slice();
    const frames = videoFramesRef.current.slice();
    const mimeType = audioMimeTypeRef.current || pickSupportedAudioMimeType() || 'audio/webm';

    audioChunksRef.current = [];
    videoFramesRef.current = [];
    setCapturedFrameCount(0);
    setElapsedSeconds(0);
    clearTimers();
    detachStream();

    if (!emitResultRef.current) {
      emitResultRef.current = false;
      recorderRef.current = null;
      audioMimeTypeRef.current = '';
      return;
    }

    emitResultRef.current = false;
    recorderRef.current = null;
    audioMimeTypeRef.current = '';
    const audioBlob = new Blob(chunks, { type: mimeType });
    const audioBase64 = await blobToBase64(audioBlob);
    onCaptureComplete(audioBase64, frames);
  }, [clearTimers, detachStream, onCaptureComplete]);

  const stopRecording = useCallback(() => {
    if (!isRecording) return;

    setIsRecording(false);
    clearTimers();

    const recorder = recorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      try {
        recorder.stop();
      } catch (err) {
        emitResultRef.current = false;
        detachStream();
        setError(err instanceof Error ? err.message : 'Impossible d’arrêter l’enregistrement');
      }
      return;
    }

    emitResultRef.current = false;
    detachStream();
  }, [clearTimers, detachStream, isRecording]);

  const startRecording = useCallback(async () => {
    if (isRecording || isInitializing) return;

    setError(null);
    setIsInitializing(true);

    try {
      if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
        throw new Error('La capture média n’est pas supportée par ce navigateur.');
      }

      if (typeof MediaRecorder === 'undefined') {
        throw new Error('MediaRecorder n’est pas disponible dans ce navigateur.');
      }

      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      streamRef.current = stream;

      const video = videoRef.current;
      if (video) {
        video.srcObject = stream;
        await video.play().catch(() => undefined);
      }

      const audioTracks = stream.getAudioTracks();
      if (audioTracks.length === 0) {
        throw new Error('Aucun micro n’a été détecté.');
      }

      const audioOnlyStream = new MediaStream(audioTracks);
      const mimeType = pickSupportedAudioMimeType();
      const recorder = mimeType ? new MediaRecorder(audioOnlyStream, { mimeType }) : new MediaRecorder(audioOnlyStream);
      audioMimeTypeRef.current = recorder.mimeType || mimeType || 'audio/webm';

      audioChunksRef.current = [];
      videoFramesRef.current = [];
      setCapturedFrameCount(0);
      setElapsedSeconds(0);

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      recorder.onstop = () => {
        void finalizeCapture().catch((captureError) => {
          setError(captureError instanceof Error ? captureError.message : 'Échec de finalisation de l’entretien');
        });
      };
      recorder.onerror = () => {
        setError('Une erreur est survenue pendant l’enregistrement audio.');
      };

      recorderRef.current = recorder;
      emitResultRef.current = true;
      recorder.start();
      setIsRecording(true);

      elapsedTimerRef.current = window.setInterval(() => {
        setElapsedSeconds((current) => current + 1);
      }, 1000);
      captureFrame();
      snapshotTimerRef.current = window.setInterval(captureFrame, snapshotIntervalMs);
    } catch (captureError) {
      clearTimers();
      detachStream();
      recorderRef.current = null;
      audioMimeTypeRef.current = '';
      audioChunksRef.current = [];
      videoFramesRef.current = [];
      setCapturedFrameCount(0);
      setIsRecording(false);
      setElapsedSeconds(0);
      setError(captureError instanceof Error ? captureError.message : 'Impossible de démarrer l’entretien');
    } finally {
      setIsInitializing(false);
    }
  }, [captureFrame, clearTimers, detachStream, finalizeCapture, isInitializing, isRecording, snapshotIntervalMs]);

  useEffect(() => {
    return () => {
      emitResultRef.current = false;
      clearTimers();
      const recorder = recorderRef.current;
      if (recorder && recorder.state !== 'inactive') {
        try {
          recorder.stop();
        } catch {
          // Ignore teardown errors.
        }
      }
      detachStream();
    };
  }, [clearTimers, detachStream]);

  return (
    <section className={`rounded-3xl border border-white/10 bg-slate-950/80 p-6 text-white shadow-2xl shadow-cyan-950/20 backdrop-blur ${className ?? ''}`}>
      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-4 lg:max-w-2xl">
          <div className="space-y-2">
            <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/70">Habits Phase 6</p>
            <h2 className="text-2xl font-semibold text-white">{title}</h2>
            <p className="max-w-2xl text-sm leading-6 text-slate-300">
              Active la caméra et le micro, capture l&apos;audio de l&apos;entretien et prélève des snapshots vidéo réguliers pour l&apos;analyse multimodale.
            </p>
          </div>

          <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/30">
            <div className="relative aspect-video bg-slate-900">
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                className="h-full w-full object-cover"
              />

              {!isRecording && !isInitializing && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-slate-950/65 text-center">
                  <Camera className="h-10 w-10 text-cyan-300" />
                  <p className="text-sm text-slate-200">Prêt à démarrer l&apos;entretien</p>
                  <p className="text-xs text-slate-400">Clique sur &quot;Démarrer l&apos;entretien&quot; pour demander l&apos;accès caméra et micro.</p>
                </div>
              )}

              {isRecording && (
                <div className="absolute left-4 top-4 flex items-center gap-2 rounded-full border border-rose-400/30 bg-rose-500/15 px-3 py-1 text-xs font-semibold text-rose-100">
                  <span className="inline-flex h-2.5 w-2.5 animate-pulse rounded-full bg-rose-400" />
                  <CircleDot className="h-3.5 w-3.5" />
                  REC
                </div>
              )}

              <div className="absolute bottom-4 left-4 rounded-full border border-white/10 bg-black/50 px-3 py-1 text-xs text-slate-100 backdrop-blur">
                {formattedTime}
              </div>

              <div className="absolute bottom-4 right-4 rounded-full border border-white/10 bg-black/50 px-3 py-1 text-xs text-slate-100 backdrop-blur">
                {capturedFrameCount} frame{capturedFrameCount > 1 ? 's' : ''}
              </div>
            </div>
          </div>

          <canvas ref={canvasRef} aria-hidden="true" className="hidden" />
        </div>

        <div className="flex w-full flex-col gap-4 lg:max-w-sm">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-white">
              <Mic className="h-4 w-4 text-cyan-300" />
              Enregistrement multimodal
            </div>

            <ul className="space-y-2 text-sm text-slate-300">
              <li>• Autorisation caméra et micro demandée au démarrage</li>
              <li>• Audio enregistré via <span className="font-medium text-slate-100">MediaRecorder</span></li>
              <li>• Snapshots vidéo capturés toutes les {Math.round(snapshotIntervalMs / 1000)} secondes</li>
              <li>• Retour en Base64 pour l&apos;API Habits</li>
            </ul>
          </div>

          <div className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/5 p-4">
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isInitializing}
              className={`inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition ${
                isRecording
                  ? 'bg-rose-500 text-white hover:bg-rose-400'
                  : 'bg-cyan-400 text-slate-950 hover:bg-cyan-300'
              } disabled:cursor-not-allowed disabled:opacity-60`}
            >
              {isRecording ? <Square className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              {isRecording ? 'Arrêter' : isInitializing ? 'Activation...' : 'Démarrer l’entretien'}
            </button>

            {error && (
              <div className="rounded-xl border border-rose-400/20 bg-rose-500/10 p-3 text-sm text-rose-100">
                {error}
              </div>
            )}

            <div className="rounded-xl border border-white/10 bg-slate-950/40 p-3 text-xs text-slate-300">
              <p className="font-medium text-slate-100">Conseil</p>
              <p className="mt-1 leading-5">
                Parle naturellement face à la caméra. Le composant te renverra un <span className="font-medium text-slate-100">audioBase64</span> et une liste de <span className="font-medium text-slate-100">videoFramesBase64</span> à transmettre au backend Habits.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
