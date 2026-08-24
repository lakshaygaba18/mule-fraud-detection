import 'package:flutter/material.dart';
import '../models/fraud_account.dart';

class AccountDetailScreen extends StatelessWidget {
  final FraudAccount account;

  const AccountDetailScreen({super.key, required this.account});

  Color _riskColor(double score) {
    if (score >= 70) return Colors.red;
    if (score >= 40) return Colors.orange;
    return Colors.green;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(account.accountId)),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Column(
                children: [
                  Text(
                    '${account.riskScore.toStringAsFixed(1)}',
                    style: TextStyle(
                      fontSize: 56,
                      fontWeight: FontWeight.bold,
                      color: _riskColor(account.riskScore),
                    ),
                  ),
                  Text(
                    'RISK SCORE / 100',
                    style: TextStyle(
                      color: Colors.grey[600],
                      letterSpacing: 1.5,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
            const Text(
              'WHY FLAGGED',
              style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.2),
            ),
            const SizedBox(height: 8),
            Text(
              account.reason,
              style: const TextStyle(fontSize: 16, height: 1.4),
            ),
            const SizedBox(height: 32),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: account.isActuallyFraud
                    ? Colors.red.withOpacity(0.1)
                    : Colors.green.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(
                    account.isActuallyFraud ? Icons.warning : Icons.check_circle,
                    color: account.isActuallyFraud ? Colors.red : Colors.green,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    account.isActuallyFraud
                        ? 'Confirmed mule/fraud account (ground truth)'
                        : 'Actually a normal account (ground truth)',
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}