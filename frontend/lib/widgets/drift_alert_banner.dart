import 'package:flutter/material.dart';
import '../models/drift_report.dart';

class DriftAlertBanner extends StatelessWidget {
  final DriftReport report;

  const DriftAlertBanner({super.key, required this.report});

  Color get _color {
    switch (report.overallStatus) {
      case 'major_shift':
        return Colors.red;
      case 'moderate_shift':
        return Colors.orange;
      default:
        return Colors.green;
    }
  }

  IconData get _icon {
    switch (report.overallStatus) {
      case 'major_shift':
        return Icons.warning_amber_rounded;
      case 'moderate_shift':
        return Icons.info_outline;
      default:
        return Icons.check_circle_outline;
    }
  }

  String get _headline {
    switch (report.overallStatus) {
      case 'major_shift':
        return 'Model drift detected -- retraining recommended';
      case 'moderate_shift':
        return 'Moderate drift detected -- worth watching';
      default:
        return 'Model is stable on current traffic';
    }
  }

  void _showDetails(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(_icon, color: _color),
            const SizedBox(width: 8),
            const Expanded(child: Text('Drift Monitoring Report')),
          ],
        ),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              if (report.scorePsi != null)
                Text('Risk-score PSI: ${report.scorePsi!.toStringAsFixed(3)}'),
              const SizedBox(height: 12),
              const Text(
                'Feature drift (PSI):',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              ...(() {
                final sorted = report.featurePsi.entries.toList()
                  ..sort((a, b) => b.value.compareTo(a.value));
                return sorted.map(
                  (e) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2),
                    child: Text('${e.key}: ${e.value.toStringAsFixed(3)}'),
                  ),
                );
              })(),
              if (report.alerts.isNotEmpty) ...[
                const SizedBox(height: 16),
                const Text(
                  'Alerts:',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                ...report.alerts.map(
                  (a) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Text('\u2022 $a'),
                  ),
                ),
              ],
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => _showDetails(context),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        width: double.infinity,
        margin: const EdgeInsets.fromLTRB(16, 16, 16, 0),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: _color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: _color.withOpacity(0.4)),
        ),
        child: Row(
          children: [
            Icon(_icon, color: _color),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _headline,
                    style: TextStyle(
                      color: _color,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Text(
                    'Tap for full drift report',
                    style: TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                ],
              ),
            ),
            Icon(Icons.chevron_right, color: _color),
          ],
        ),
      ),
    );
  }
}