import 'package:flutter/material.dart';
import '../models/fraud_account.dart';
import '../models/drift_report.dart';
import '../services/fraud_api_service.dart';
import '../widgets/drift_alert_banner.dart';
import 'account_detail_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final FraudApiService _apiService = FraudApiService();
  late Future<FraudReport> _reportFuture;
  late Future<DriftReport> _driftReportFuture;

  @override
  void initState() {
    super.initState();
    _reportFuture = _apiService.fetchFraudReport();
    _driftReportFuture = _apiService.fetchDriftReport();
  }

  void _refresh() {
    setState(() {
      _reportFuture = _apiService.fetchFraudReport();
      _driftReportFuture = _apiService.fetchDriftReport();
    });
  }

  Color _riskColor(double score) {
    if (score >= 70) return Colors.red;
    if (score >= 40) return Colors.orange;
    return Colors.green;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Fraud Intelligence Dashboard'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _refresh),
        ],
      ),
      body: FutureBuilder<FraudReport>(
        future: _reportFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Text(
                  'Could not reach backend.\nMake sure Spring Boot is running on port 8080.\n\n${snapshot.error}',
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }

          final report = snapshot.data!;
          final sortedResults = [...report.results]
            ..sort((a, b) => b.riskScore.compareTo(a.riskScore));

          return Column(
            children: [
              // --- Drift monitoring banner: the "self-aware" signal ---
              FutureBuilder<DriftReport>(
                future: _driftReportFuture,
                builder: (context, driftSnapshot) {
                  if (driftSnapshot.connectionState ==
                      ConnectionState.waiting) {
                    return const Padding(
                      padding: EdgeInsets.all(16),
                      child: LinearProgressIndicator(),
                    );
                  }
                  if (driftSnapshot.hasError || !driftSnapshot.hasData) {
                    // Drift service failing shouldn't block the main dashboard
                    return const SizedBox.shrink();
                  }
                  return DriftAlertBanner(report: driftSnapshot.data!);
                },
              ),

              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Expanded(
                      child: _StatCard(
                        label: 'Accounts Scored',
                        value: '${report.totalAccountsScored}',
                        color: Colors.blue,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _StatCard(
                        label: 'Flagged as Risky',
                        value: '${report.flaggedCount}',
                        color: Colors.red,
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: ListView.builder(
                  itemCount: sortedResults.length,
                  itemBuilder: (context, index) {
                    final account = sortedResults[index];
                    return ListTile(
                      leading: CircleAvatar(
                        backgroundColor: _riskColor(account.riskScore),
                        child: Text(
                          account.riskScore.toStringAsFixed(0),
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                          ),
                        ),
                      ),
                      title: Text(account.accountId),
                      subtitle: Text(
                        account.reason,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => AccountDetailScreen(account: account),
                          ),
                        );
                      },
                    );
                  },
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _StatCard({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            value,
            style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: color),
          ),
          Text(label, style: TextStyle(color: Colors.grey[700])),
        ],
      ),
    );
  }
}