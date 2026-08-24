class DriftReport {
  final String overallStatus;
  final double? scorePsi;
  final Map<String, double> featurePsi;
  final double? explanationJsDivergence;
  final List<String> alerts;
  final String summaryText;

  DriftReport({
    required this.overallStatus,
    required this.scorePsi,
    required this.featurePsi,
    required this.explanationJsDivergence,
    required this.alerts,
    required this.summaryText,
  });

  factory DriftReport.fromJson(Map<String, dynamic> json) {
    final rawFeaturePsi = json['feature_psi'] as Map<String, dynamic>? ?? {};

    return DriftReport(
      overallStatus: json['overall_status'] as String? ?? 'unknown',
      scorePsi: (json['score_psi'] as num?)?.toDouble(),
      featurePsi: rawFeaturePsi.map(
        (key, value) => MapEntry(key, (value as num).toDouble()),
      ),
      explanationJsDivergence:
          (json['explanation_js_divergence'] as num?)?.toDouble(),
      alerts: (json['alerts'] as List? ?? [])
          .map((e) => e.toString())
          .toList(),
      summaryText: json['summary_text'] as String? ?? '',
    );
  }

  bool get isStable => overallStatus == 'stable';
  bool get isMajorShift => overallStatus == 'major_shift';
}