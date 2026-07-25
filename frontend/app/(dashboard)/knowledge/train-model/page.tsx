'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { getKnowledgeModelStatus, trainKnowledgeModel, predictFiliere, uploadTrainingCv, listTrainingCvs, getTrainingHistory, predictFilierePdf } from '@/lib/api';
import { Brain, Upload, Zap, CheckCircle, XCircle, Loader2, BarChart3, Target, ShieldAlert, FileText, Plus, TrendingUp } from 'lucide-react';

interface ModelStatus {
  is_trained: boolean;
  classes: string[];
  n_features: number;
  training_report: any;
}

interface PredictionResult {
  predicted_filiere: string;
  probabilities: { filiere: string; probability: number }[];
  cluster: number;
  tfidf_knn_score: number;
  top_similarities: [string, number][];
  confidence: string;
  confidence_margin: number;
  detected_tech_domains: Record<string, number>;
  detected_skills: string[];
  n_features_matched: number;
  source?: string;
  filename?: string;
  extracted_text_length?: number;
}

export default function TrainModelPage() {
  const { user, loading: authLoading } = useAuth();
  const [status, setStatus] = useState<ModelStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [training, setTraining] = useState(false);
  const [trainResult, setTrainResult] = useState<any>(null);
  const [trainError, setTrainError] = useState<string | null>(null);

  const [cvText, setCvText] = useState('');
  const [predicting, setPredicting] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [predictError, setPredictError] = useState<string | null>(null);

  // Upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadFiliere, setUploadFiliere] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [trainingCvs, setTrainingCvs] = useState<{ filename: string; filiere: string; skills_count: number; text_length: number }[]>([]);
  const [loadingCvs, setLoadingCvs] = useState(false);
  const [trainingHistory, setTrainingHistory] = useState<{ trained_at: string; cv_accuracy: number; train_accuracy: number; n_samples: number; n_samples_after_smote: number; n_features: number; smote_applied: boolean; best_algorithm: string }[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pdfPredicting, setPdfPredicting] = useState(false);
  const [pdfPrediction, setPdfPrediction] = useState<PredictionResult | null>(null);
  const [pdfPredictError, setPdfPredictError] = useState<string | null>(null);

  const FILIERES = [
    'Génie Électrique',
    'Génie Mécanique',
    'Génie Industriel',
    'Contrôle & Maintenance (CMPI)',
    'Qualité & Maintenance (QMSI)',
    'Logistique',
  ];

  const isAdmin = user?.is_admin === true;

  const fetchStatus = useCallback(async () => {
    if (!isAdmin) { setLoadingStatus(false); return; }
    setLoadingStatus(true);
    try {
      const s = await getKnowledgeModelStatus();
      setStatus(s);
    } catch {
      setStatus(null);
    } finally {
      setLoadingStatus(false);
    }
  }, [isAdmin]);

  const fetchTrainingCvs = useCallback(async () => {
    if (!isAdmin) return;
    setLoadingCvs(true);
    try {
      const res = await listTrainingCvs();
      setTrainingCvs(res.cvs);
    } catch {
      setTrainingCvs([]);
    } finally {
      setLoadingCvs(false);
    }
  }, [isAdmin]);

  const fetchTrainingHistory = useCallback(async () => {
    if (!isAdmin) return;
    setLoadingHistory(true);
    try {
      const res = await getTrainingHistory();
      setTrainingHistory(res.history);
    } catch {
      setTrainingHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  }, [isAdmin]);

  useEffect(() => {
    fetchStatus();
    fetchTrainingCvs();
    fetchTrainingHistory();
  }, [fetchStatus, fetchTrainingCvs, fetchTrainingHistory]);

  const handleTrain = async () => {
    setTraining(true);
    setTrainError(null);
    setTrainResult(null);
    try {
      const result = await trainKnowledgeModel();
      setTrainResult(result);
      fetchStatus();
      fetchTrainingCvs();
    } catch (e: any) {
      setTrainError(e.message || 'Training failed');
    } finally {
      setTraining(false);
    }
  };

  const handlePdfPredict = async () => {
    if (!pdfFile) return;
    setPdfPredicting(true);
    setPdfPredictError(null);
    setPdfPrediction(null);
    try {
      const result = await predictFilierePdf(pdfFile);
      setPdfPrediction(result);
    } catch (e: any) {
      setPdfPredictError(e.message || 'PDF prediction failed');
    } finally {
      setPdfPredicting(false);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile || !uploadFiliere) return;
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const result = await uploadTrainingCv(uploadFile, uploadFiliere);
      setUploadResult(result);
      setUploadFile(null);
      setUploadFiliere('');
      fetchTrainingCvs();
    } catch (e: any) {
      setUploadError(e.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handlePredict = async () => {
    if (cvText.trim().length < 50) return;
    setPredicting(true);
    setPredictError(null);
    setPrediction(null);
    try {
      const result = await predictFiliere(cvText);
      setPrediction(result);
    } catch (e: any) {
      setPredictError(e.message || 'Prediction failed');
    } finally {
      setPredicting(false);
    }
  };

  if (authLoading) {
    return (
      <main className="mx-auto flex max-w-6xl items-center justify-center px-4 py-20">
        <Loader2 className="h-8 w-8 animate-spin text-aurora" />
      </main>
    );
  }

  if (!isAdmin) {
    return (
      <main className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 lg:px-0">
        <div className="flex items-center justify-between gap-3 flex-wrap text-sm text-white/70">
          <Link href="/" className="text-mist hover:text-white transition">
            ← Back to dashboard
          </Link>
        </div>
        <section className="glass-panel p-12 flex flex-col items-center text-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/20">
            <ShieldAlert className="h-8 w-8 text-red-400" />
          </div>
          <h1 className="text-2xl font-bold">Admin Access Required</h1>
          <p className="text-sm text-white/60 max-w-md">
            This page is restricted to KASH platform administrators. Only admins can train and manage the Knowledge ML model.
          </p>
          <Link href="/" className="mt-2 rounded-lg bg-white/10 px-6 py-2 text-sm transition hover:bg-white/20">
            Return to dashboard
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 lg:px-0">
      <div className="flex items-center justify-between gap-3 flex-wrap text-sm text-white/70">
        <Link href="/" className="text-mist hover:text-white transition">
          ← Back to dashboard
        </Link>
        <span className="text-xs text-white/60">KASH Knowledge (K) — ML Model Training (Admin)</span>
      </div>

      {/* Header */}
      <section className="glass-panel p-8">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-aurora/20">
            <Brain className="h-7 w-7 text-aurora" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">KASH Knowledge Model</h1>
            <p className="text-sm text-white/60 mt-1">
              Pipeline: Data Cleaning → NLTK Tokenization → Stemming → TF-IDF → KNN Similarity
            </p>
          </div>
        </div>
      </section>

      {/* Model Status */}
      <section className="glass-panel p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-aurora" />
            Model Status
          </h2>
          <button
            onClick={fetchStatus}
            className="text-xs text-mist hover:text-white transition"
          >
            Refresh
          </button>
        </div>

        {loadingStatus ? (
          <div className="flex items-center gap-2 mt-4 text-white/60">
            <Loader2 className="h-4 w-4 animate-spin" /> Checking model...
          </div>
        ) : status?.is_trained ? (
          <div className="mt-4 space-y-3">
            <div className="flex items-center gap-2 text-green-400">
              <CheckCircle className="h-5 w-5" />
              <span className="font-medium">Model is trained and ready</span>
            </div>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="rounded-lg bg-white/5 p-3">
                <p className="text-xs text-white/50">Classes</p>
                <p className="text-lg font-bold">{status.classes.length}</p>
              </div>
              <div className="rounded-lg bg-white/5 p-3">
                <p className="text-xs text-white/50">Features</p>
                <p className="text-lg font-bold">{status.n_features}</p>
              </div>
              {status.training_report && (
                <>
                  <div className="rounded-lg bg-white/5 p-3">
                    <p className="text-xs text-white/50">Train Accuracy</p>
                    <p className="text-lg font-bold">{(status.training_report.train_accuracy * 100).toFixed(1)}%</p>
                  </div>
                  <div className="rounded-lg bg-white/5 p-3">
                    <p className="text-xs text-white/50">CV Accuracy</p>
                    <p className="text-lg font-bold text-aurora">{(status.training_report.cv_accuracy * 100).toFixed(1)}%</p>
                  </div>
                </>
              )}
            </div>
            {status.training_report?.smote_applied && (
              <div className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 px-3 py-1 text-xs text-emerald-300">
                <CheckCircle className="h-3 w-3" /> SMOTE applied: {status.training_report.n_samples} → {status.training_report.n_samples_after_smote} samples
              </div>
            )}
            {status.classes.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {status.classes.map((cls) => (
                  <span key={cls} className="rounded-full bg-aurora/20 px-3 py-1 text-xs text-aurora">
                    {cls}
                  </span>
                ))}
              </div>
            )}
            {status.training_report?.best_algorithm && (
              <p className="text-xs text-white/50 mt-2">
                Best algorithm: <span className="text-white/80">{status.training_report.best_algorithm}</span>
                {' · '}Model: <span className="text-white/80">{status.training_report.model_type}</span>
              </p>
            )}
          </div>
        ) : (
          <div className="mt-4 flex items-center gap-2 text-yellow-400">
            <XCircle className="h-5 w-5" />
            <span>Model not trained yet. Click "Train Model" below.</span>
          </div>
        )}
      </section>

      {/* Training History */}
      <section className="glass-panel p-6">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-aurora" />
            Training History
          </h2>
          <span className="text-xs text-white/40">
            {loadingHistory ? 'Loading...' : `${trainingHistory.length} training run${trainingHistory.length > 1 ? 's' : ''}`}
          </span>
        </div>

        {trainingHistory.length > 0 ? (
          <div className="mt-4 space-y-3">
            <div className="flex items-end gap-2 overflow-x-auto pb-2">
              {trainingHistory.slice(-12).map((run, idx) => {
                const height = Math.max(18, Math.round(run.cv_accuracy * 160));
                return (
                  <div key={`${run.trained_at}-${idx}`} className="flex min-w-[72px] flex-col items-center gap-2">
                    <div className="flex h-44 w-full items-end rounded-lg bg-white/5 p-2">
                      <div
                        className="w-full rounded-md bg-aurora/80 hover:bg-aurora transition"
                        style={{ height: `${height}px` }}
                        title={`CV ${(run.cv_accuracy * 100).toFixed(1)}% · Train ${(run.train_accuracy * 100).toFixed(1)}%`}
                      />
                    </div>
                    <div className="text-center text-[10px] text-white/50">
                      <div>{new Date(run.trained_at).toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' })}</div>
                      <div className="text-aurora font-semibold">{(run.cv_accuracy * 100).toFixed(1)}%</div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-lg bg-white/5 p-4">
                <p className="text-xs text-white/50">Best CV Accuracy</p>
                <p className="text-2xl font-bold text-emerald-300">
                  {Math.max(...trainingHistory.map((r) => r.cv_accuracy), 0).toFixed(3)}
                </p>
              </div>
              <div className="rounded-lg bg-white/5 p-4">
                <p className="text-xs text-white/50">Latest Algorithm</p>
                <p className="text-sm font-semibold text-white/80">
                  {trainingHistory[trainingHistory.length - 1]?.best_algorithm ?? '—'}
                </p>
              </div>
              <div className="rounded-lg bg-white/5 p-4">
                <p className="text-xs text-white/50">SMOTE on latest run</p>
                <p className="text-sm font-semibold text-white/80">
                  {trainingHistory[trainingHistory.length - 1]?.smote_applied ? 'Enabled' : 'Disabled'}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <p className="mt-4 text-sm text-white/50">No training history yet. Train the model at least once to populate the chart.</p>
        )}
      </section>

      {/* Upload CV Section */}
      <section className="glass-panel p-6">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Plus className="h-5 w-5 text-aurora" />
          Add CV to Training Corpus
        </h2>
        <p className="text-sm text-white/60 mt-2">
          Upload a new CV PDF with its filiere to add it to the training data. After uploading, click "Train Model" to re-train with the new CV included.
        </p>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <label className="text-xs text-white/50">CV PDF File</label>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
              className="mt-1 block w-full text-sm text-white/70 file:mr-3 file:rounded-lg file:border-0 file:bg-aurora/20 file:px-4 file:py-2 file:text-sm file:text-aurora hover:file:bg-aurora/30"
            />
          </div>
          <div>
            <label className="text-xs text-white/50">Filiere</label>
            <select
              value={uploadFiliere}
              onChange={(e) => setUploadFiliere(e.target.value)}
              className="mt-1 block w-full rounded-lg bg-white/5 px-3 py-2 text-sm text-white border border-white/10 focus:border-aurora focus:outline-none"
            >
              <option value="" className="bg-midnight">Select filiere...</option>
              {FILIERES.map((f) => (
                <option key={f} value={f} className="bg-midnight">{f}</option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleUpload}
          disabled={!uploadFile || !uploadFiliere || uploading}
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-aurora/20 px-4 py-2 text-sm font-medium text-aurora transition hover:bg-aurora/30 disabled:opacity-40"
        >
          {uploading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" /> Uploading...
            </>
          ) : (
            <>
              <Upload className="h-4 w-4" /> Upload CV
            </>
          )}
        </button>

        {uploadError && (
          <div className="mt-3 rounded-lg bg-red-500/10 p-3 text-sm text-red-400">{uploadError}</div>
        )}

        {uploadResult && (
          <div className="mt-3 rounded-lg bg-green-500/10 p-4 text-sm">
            <div className="flex items-center gap-2 text-green-400">
              <CheckCircle className="h-4 w-4" />
              <span className="font-medium">CV {uploadResult.action} successfully!</span>
            </div>
            <p className="text-white/60 mt-1">
              File: <span className="text-white/80">{uploadResult.filename}</span>
              {' · '}Filiere: <span className="text-white/80">{uploadResult.filiere}</span>
              {' · '}Skills: <span className="text-white/80">{uploadResult.n_skills}</span>
              {' · '}Total CVs: <span className="text-white/80">{uploadResult.total_cvs}</span>
            </p>
            {uploadResult.skills_extracted?.length > 0 && (
              <div className="mt-3 space-y-2">
                <p className="text-xs text-white/50">
                  Skills extraites: <span className="text-white/85">{uploadResult.skills_extracted.join(' · ')}</span>
                </p>
                <div className="flex flex-wrap gap-2">
                  {uploadResult.skills_extracted.map((s: string) => (
                    <span key={s} className="rounded-full bg-aurora/15 px-3 py-1 text-xs text-aurora">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <p className="text-yellow-400 mt-2 text-xs">Now click "Train Model" to include this CV in the model.</p>
          </div>
        )}

        {/* Training corpus list */}
        <div className="mt-6">
          <p className="text-sm font-medium text-white/70 mb-2 flex items-center gap-2">
            <FileText className="h-4 w-4" /> Training Corpus ({trainingCvs.length} CVs)
          </p>
          {loadingCvs ? (
            <Loader2 className="h-4 w-4 animate-spin text-aurora" />
          ) : (
            <div className="max-h-48 overflow-y-auto space-y-1">
              {trainingCvs.map((cv) => (
                <div key={cv.filename} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2 text-xs">
                  <span className="text-white/70 truncate max-w-[60%]">{cv.filename}</span>
                  <span className="text-aurora">{cv.filiere}</span>
                  <span className="text-white/40">{cv.skills_count} skills</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* PDF Prediction Section */}
      <section className="glass-panel p-6">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <FileText className="h-5 w-5 text-aurora" />
          Quick Prediction from PDF
        </h2>
        <p className="text-sm text-white/60 mt-2">
          Upload a CV PDF and let KASH extract the text automatically before predicting the filiere.
        </p>

        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label className="text-xs text-white/50">CV PDF File</label>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setPdfFile(e.target.files?.[0] ?? null)}
              className="mt-1 block w-full text-sm text-white/70 file:mr-3 file:rounded-lg file:border-0 file:bg-aurora/20 file:px-4 file:py-2 file:text-sm file:text-aurora hover:file:bg-aurora/30"
            />
          </div>
          <button
            onClick={handlePdfPredict}
            disabled={!pdfFile || pdfPredicting || !status?.is_trained}
            className="inline-flex items-center gap-2 rounded-lg bg-aurora px-5 py-3 text-sm font-semibold text-midnight transition hover:bg-aurora/80 disabled:opacity-50"
          >
            {pdfPredicting ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
            Predict from PDF
          </button>
        </div>

        {pdfPredictError && (
          <div className="mt-4 rounded-lg bg-red-500/10 p-4 text-sm text-red-400">{pdfPredictError}</div>
        )}

        {pdfPrediction && (
          <div className="mt-6 rounded-lg bg-aurora/10 p-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div>
                <p className="text-xs text-white/50">Predicted Filiere</p>
                <p className="text-2xl font-bold text-aurora">{pdfPrediction.predicted_filiere}</p>
              </div>
              <div className="text-xs text-white/60">
                Source: <span className="text-white/80">{pdfPrediction.source ?? 'pdf'}</span>
                {' · '}Text length: <span className="text-white/80">{pdfPrediction.extracted_text_length ?? '—'}</span>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Training Section */}
      <section className="glass-panel p-6">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Zap className="h-5 w-5 text-aurora" />
          Train the Model
        </h2>
        <p className="text-sm text-white/60 mt-2">
          Trains the KASH Knowledge ML model on the ENSEM CV corpus using TF-IDF + classifier comparison
          (RandomForest, SVM, LogisticRegression). The best model is automatically saved and used by the platform.
        </p>

        <button
          onClick={handleTrain}
          disabled={training}
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-aurora px-6 py-3 font-medium text-midnight transition hover:bg-aurora/80 disabled:opacity-50"
        >
          {training ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" /> Training in progress...
            </>
          ) : (
            <>
              <Zap className="h-4 w-4" /> Train Model
            </>
          )}
        </button>

        {trainError && (
          <div className="mt-4 rounded-lg bg-red-500/10 p-4 text-sm text-red-400">
            {trainError}
          </div>
        )}

        {trainResult && !trainResult.error && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center gap-2 text-green-400">
              <CheckCircle className="h-5 w-5" />
              <span className="font-medium">Training completed successfully!</span>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-lg bg-white/5 p-4">
                <p className="text-xs text-white/50">Samples</p>
                <p className="text-2xl font-bold">{trainResult.n_samples}</p>
              </div>
              <div className="rounded-lg bg-white/5 p-4">
                <p className="text-xs text-white/50">Features</p>
                <p className="text-2xl font-bold">{trainResult.n_features}</p>
              </div>
              <div className="rounded-lg bg-white/5 p-4">
                <p className="text-xs text-white/50">Best Algorithm</p>
                <p className="text-lg font-bold">{trainResult.best_algorithm}</p>
              </div>
            </div>

            {trainResult.algorithm_comparison && (
              <div>
                <p className="text-sm font-medium text-white/70 mb-2">Algorithm Comparison</p>
                <div className="space-y-2">
                  {Object.entries(trainResult.algorithm_comparison).map(([name, data]: [string, any]) => (
                    <div key={name} className="flex items-center justify-between rounded-lg bg-white/5 p-3">
                      <span className="text-sm">{name}</span>
                      <div className="flex items-center gap-3">
                        <div className="h-2 w-32 rounded-full bg-white/10">
                          <div
                            className="h-2 rounded-full bg-aurora"
                            style={{ width: `${data.cv_accuracy * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-mono text-white/70">
                          {(data.cv_accuracy * 100).toFixed(1)}% ± {data.cv_std}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {trainResult.confusion_matrix && trainResult.classes && (
              <div>
                <p className="text-sm font-medium text-white/70 mb-2">Confusion Matrix</p>
                <div className="overflow-x-auto">
                  <table className="text-xs">
                    <thead>
                      <tr>
                        <th className="p-2"></th>
                        {trainResult.classes.map((cls: string) => (
                          <th key={cls} className="p-2 text-white/60">{cls.slice(0, 12)}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {trainResult.confusion_matrix.map((row: number[], i: number) => (
                        <tr key={i}>
                          <td className="p-2 text-white/60 font-medium">{trainResult.classes[i]?.slice(0, 12)}</td>
                          {row.map((val: number, j: number) => (
                            <td
                              key={j}
                              className={`p-2 text-center ${val > 0 ? 'bg-aurora/20 font-bold' : ''}`}
                            >
                              {val}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {trainResult.feature_importance?.global?.length > 0 && (
              <div>
                <p className="text-sm font-medium text-white/70 mb-2">Top Features (Global Importance)</p>
                <div className="flex flex-wrap gap-2">
                  {trainResult.feature_importance.global.slice(0, 15).map((f: any) => (
                    <span key={f.feature} className="rounded-full bg-white/5 px-3 py-1 text-xs">
                      {f.feature} <span className="text-aurora">{f.importance}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Prediction Section */}
      <section className="glass-panel p-6">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Target className="h-5 w-5 text-aurora" />
          Test Prediction
        </h2>
        <p className="text-sm text-white/60 mt-2">
          Paste CV text below to predict the filiere using the trained model.
        </p>

        <textarea
          value={cvText}
          onChange={(e) => setCvText(e.target.value)}
          placeholder="Paste CV text here (min 50 characters)..."
          className="mt-4 w-full rounded-lg bg-white/5 p-4 text-sm text-white/90 placeholder-white/30 outline-none focus:ring-2 focus:ring-aurora/50 min-h-[200px] resize-y"
        />

        <button
          onClick={handlePredict}
          disabled={predicting || cvText.trim().length < 50 || !status?.is_trained}
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-white/10 px-6 py-3 font-medium transition hover:bg-white/20 disabled:opacity-50"
        >
          {predicting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" /> Predicting...
            </>
          ) : (
            <>
              <Target className="h-4 w-4" /> Predict Filiere
            </>
          )}
        </button>

        {!status?.is_trained && (
          <p className="mt-2 text-xs text-yellow-400">Train the model first before testing predictions.</p>
        )}

        {predictError && (
          <div className="mt-4 rounded-lg bg-red-500/10 p-4 text-sm text-red-400">
            {predictError}
          </div>
        )}

        {prediction && (
          <div className="mt-6 space-y-4">
            <div className="rounded-lg bg-aurora/10 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-white/50">Predicted Filiere</p>
                  <p className="text-2xl font-bold text-aurora">{prediction.predicted_filiere}</p>
                </div>
                <div className={`rounded-full px-3 py-1 text-xs font-bold ${
                  prediction.confidence === 'high' ? 'bg-green-500/20 text-green-400' :
                  prediction.confidence === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-red-500/20 text-red-400'
                }`}>
                  {prediction.confidence?.toUpperCase()} confidence
                </div>
              </div>
              <p className="text-xs text-white/50 mt-2">
                TF-IDF/KNN Score: <span className="text-white/80">{(prediction.tfidf_knn_score * 100).toFixed(1)}%</span>
                {' · '}Cluster: <span className="text-white/80">{prediction.cluster}</span>
                {' · '}Margin: <span className="text-white/80">{(prediction.confidence_margin * 100).toFixed(1)}%</span>
                {' · '}Features matched: <span className="text-white/80">{prediction.n_features_matched}</span>
              </p>
            </div>

            <div>
              <p className="text-sm font-medium text-white/70 mb-2">Probabilities by Filiere</p>
              <div className="space-y-2">
                {prediction.probabilities.map((p) => (
                  <div key={p.filiere} className="flex items-center justify-between rounded-lg bg-white/5 p-3">
                    <span className="text-sm">{p.filiere}</span>
                    <div className="flex items-center gap-3">
                      <div className="h-2 w-32 rounded-full bg-white/10">
                        <div
                          className="h-2 rounded-full bg-aurora"
                          style={{ width: `${p.probability * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-mono text-white/70">{(p.probability * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {prediction.detected_skills?.length > 0 && (
              <div>
                <p className="text-sm font-medium text-white/70 mb-2">Detected Technical Skills</p>
                <div className="flex flex-wrap gap-2">
                  {prediction.detected_skills.map((skill) => (
                    <span key={skill} className="rounded-full bg-aurora/20 px-3 py-1 text-xs text-aurora">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {prediction.detected_tech_domains && Object.keys(prediction.detected_tech_domains).length > 0 && (
              <div>
                <p className="text-sm font-medium text-white/70 mb-2">Technical Domain Signals</p>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                  {Object.entries(prediction.detected_tech_domains).map(([domain, hits]) => (
                    <div key={domain} className="rounded-lg bg-white/5 p-3">
                      <p className="text-xs text-white/50 capitalize">{domain}</p>
                      <p className="text-lg font-bold">{hits} <span className="text-xs text-white/40">keywords</span></p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {prediction.top_similarities?.length > 0 && (
              <div>
                <p className="text-sm font-medium text-white/70 mb-2">Top TF-IDF/KNN Similarities</p>
                <div className="space-y-1">
                  {prediction.top_similarities.map(([label, sim]: [string, number]) => (
                    <div key={label} className="flex items-center justify-between text-sm">
                      <span className="text-white/70">{label}</span>
                      <span className="font-mono text-aurora">{(sim * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
