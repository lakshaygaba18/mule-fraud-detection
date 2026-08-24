class FraudAccount {
  final String accountId;
  final double riskScore;
  final String reason;
  final int label;

  FraudAccount({
    required this.accountId,
    required this.riskScore,
    required this.reason,
    required this.label,
  });

  factory FraudAccount.fromJson(Map<String, dynamic> json) {
    return FraudAccount(
      accountId: json['account_id'] as String,
      riskScore: (json['risk_score'] as num).toDouble(),
      reason: json['reason'] as String,
      label: json['label'] as int,
    );
  }

  bool get isActuallyFraud => label == 1;
}

class FraudReport {
  final int totalAccountsScored;
  final int flaggedCount;
  final List<FraudAccount> results;

  FraudReport({
    required this.totalAccountsScored,
    required this.flaggedCount,
    required this.results,
  });

  factory FraudReport.fromJson(Map<String, dynamic> json) {
    return FraudReport(
      totalAccountsScored: json['total_accounts_scored'] as int,
      flaggedCount: json['flagged_count'] as int,
      results: (json['results'] as List)
          .map((item) => FraudAccount.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}