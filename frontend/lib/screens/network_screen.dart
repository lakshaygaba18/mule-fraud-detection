import 'package:flutter/material.dart';
import 'package:graphview/GraphView.dart';

import '../models/network_graph.dart';
import '../services/fraud_api_service.dart';

class NetworkScreen extends StatefulWidget {
  const NetworkScreen({super.key});

  @override
  State<NetworkScreen> createState() => _NetworkScreenState();
}

class _NetworkScreenState extends State<NetworkScreen> {
  final FraudApiService _apiService = FraudApiService();

  late Future<NetworkGraph> _networkFuture;

  final GraphViewController _controller = GraphViewController();

  String? _selectedNodeId;
  String _filter = 'ALL';

  @override
  void initState() {
    super.initState();
    _networkFuture = _apiService.fetchNetwork();
  }

  void _refresh() {
    setState(() {
      _selectedNodeId = null;
      _networkFuture = _apiService.fetchNetwork();
    });
  }

  // ============================================================
  // RISK
  // ============================================================

  Color _riskColor(String risk) {
    switch (risk.toUpperCase()) {
      case 'HIGH':
        return const Color(0xFFFF4D5A);

      case 'UNCERTAIN':
        return const Color(0xFFFFB020);

      case 'LOW':
        return const Color(0xFF2DD4BF);

      default:
        return const Color(0xFF64748B);
    }
  }

  String _calculatedRisk(NetworkNode node) {
    final score = node.riskScore;

    if (score >= 70) {
      return 'HIGH';
    }

    if (score >= 40) {
      return 'UNCERTAIN';
    }

    return 'LOW';
  }

  // ============================================================
  // ACCOUNT TYPE
  // ============================================================

  String _nodeType(String id) {
    final upperId = id.toUpperCase();

    if (upperId.startsWith('MULE_')) {
      return 'MULE';
    }

    if (upperId.startsWith('STRUCT_')) {
      return 'STRUCTURED';
    }

    if (upperId.startsWith('OUT_')) {
      return 'OUTBOUND';
    }

    return 'OTHER';
  }

  Color _typeColor(String id) {
    switch (_nodeType(id)) {
      case 'MULE':
        return const Color(0xFFFFB020);

      case 'STRUCTURED':
        return const Color(0xFF9B7BFF);

      case 'OUTBOUND':
        return const Color(0xFF4D8DFF);

      default:
        return const Color(0xFF94A3B8);
    }
  }

  IconData _nodeIcon(String type) {
    switch (type) {
      case 'MULE':
        return Icons.person_search_rounded;

      case 'STRUCTURED':
        return Icons.account_tree_rounded;

      case 'OUTBOUND':
        return Icons.call_made_rounded;

      default:
        return Icons.person_rounded;
    }
  }

  // ============================================================
  // HELPERS
  // ============================================================

  String _shortId(String id) {
    if (id.length <= 13) {
      return id;
    }

    return '${id.substring(0, 8)}...${id.substring(id.length - 4)}';
  }

  String _formatAmount(double amount) {
    if (amount >= 10000000) {
      return '₹${(amount / 10000000).toStringAsFixed(1)}Cr';
    }

    if (amount >= 100000) {
      return '₹${(amount / 100000).toStringAsFixed(1)}L';
    }

    if (amount >= 1000) {
      return '₹${(amount / 1000).toStringAsFixed(1)}K';
    }

    return '₹${amount.toStringAsFixed(0)}';
  }

  // ============================================================
  // BUILD
  // ============================================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF090E1D),

      appBar: AppBar(
        elevation: 0,
        backgroundColor: const Color(0xFF0E1628),
        foregroundColor: Colors.white,
        titleSpacing: 20,

        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(9),
              decoration: BoxDecoration(
                color: const Color(0xFF4D8DFF)
                    .withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(
                Icons.account_tree_rounded,
                color: Color(0xFF4D8DFF),
                size: 21,
              ),
            ),

            const SizedBox(width: 12),

            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Fraud Network Intelligence',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),

                SizedBox(height: 2),

                Text(
                  'Transaction relationship analysis',
                  style: TextStyle(
                    fontSize: 11,
                    color: Color(0xFF8B96AA),
                  ),
                ),
              ],
            ),
          ],
        ),

        actions: [
          IconButton(
            tooltip: 'Reset view',
            onPressed: () {
              _controller.resetView();
            },
            icon: const Icon(
              Icons.center_focus_strong_rounded,
            ),
          ),

          IconButton(
            tooltip: 'Refresh network',
            onPressed: _refresh,
            icon: const Icon(
              Icons.refresh_rounded,
            ),
          ),

          const SizedBox(width: 8),
        ],
      ),

      body: FutureBuilder<NetworkGraph>(
        future: _networkFuture,

        builder: (context, snapshot) {
          if (snapshot.connectionState ==
              ConnectionState.waiting) {
            return const Center(
              child: CircularProgressIndicator(
                color: Color(0xFF4D8DFF),
              ),
            );
          }

          if (snapshot.hasError) {
            return _buildError(
              snapshot.error.toString(),
            );
          }

          if (!snapshot.hasData) {
            return const Center(
              child: Text(
                'No network data available',
                style: TextStyle(
                  color: Colors.white,
                ),
              ),
            );
          }

          return _buildNetwork(
            snapshot.data!,
          );
        },
      ),
    );
  }

  // ============================================================
  // NETWORK
  // ============================================================

  Widget _buildNetwork(NetworkGraph data) {
    final nodes = data.nodes;
    final edges = data.edges;

    final filteredNodes = nodes.where((node) {
      final type = _nodeType(node.id);
      final calculatedRisk = _calculatedRisk(node);

      switch (_filter) {
        case 'ALL':
          return true;

        case 'HIGH':
          return calculatedRisk == 'HIGH';

        case 'MULE':
          return type == 'MULE';

        case 'OUT':
          return type == 'OUTBOUND';

        default:
          return true;
      }
    }).toList();

    final allowedIds = filteredNodes
        .map((node) => node.id)
        .toSet();

    // Show edges where EITHER side is a filtered account (not just both) --
    // otherwise mule/outbound accounts show zero connections, since they
    // mainly transact with senders/receivers, not with each other.
    final relevantEdges = edges.where((edge) {
      return allowedIds.contains(edge.source) ||
          allowedIds.contains(edge.target);
    }).toList();

    final contextIds = <String>{};
    for (final edge in relevantEdges) {
      contextIds.add(edge.source);
      contextIds.add(edge.target);
    }

    final nodeById = {
      for (final node in nodes) node.id: node,
    };

    final displayNodes = [
      ...filteredNodes,
      ...contextIds
          .difference(allowedIds)
          .map((id) => nodeById[id])
          .whereType<NetworkNode>(),
    ];

    final filteredEdges = relevantEdges;

    final highRiskCount = nodes
        .where(
          (node) =>
              _calculatedRisk(node) == 'HIGH',
        )
        .length;

    final muleCount = nodes
        .where(
          (node) => _nodeType(node.id) == 'MULE',
        )
        .length;

    double totalVolume = 0;

    for (final edge in edges) {
      totalVolume += edge.amount;
    }

    return Column(
      children: [
        _buildStats(
          nodes: nodes.length,
          transactions: edges.length,
          highRisk: highRiskCount,
          mules: muleCount,
          volume: totalVolume,
        ),

        _buildToolbar(
          visibleCount: filteredNodes.length,
          totalCount: nodes.length,
        ),

        Expanded(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(
              16,
              0,
              16,
              16,
            ),

            child: Row(
              children: [
                Expanded(
                  child: _buildGraph(
                    displayNodes,
                    filteredEdges,
                  ),
                ),

                if (_selectedNodeId != null)
                  const SizedBox(width: 14),

                if (_selectedNodeId != null)
                  SizedBox(
                    width: 300,
                    child: _buildSelectedPanel(
                      nodes,
                      edges,
                    ),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  // ============================================================
  // STATS
  // ============================================================

  Widget _buildStats({
    required int nodes,
    required int transactions,
    required int highRisk,
    required int mules,
    required double volume,
  }) {
    return Container(
      padding: const EdgeInsets.fromLTRB(
        16,
        14,
        16,
        12,
      ),

      child: Row(
        children: [
          Expanded(
            child: _metricCard(
              'NETWORK NODES',
              '$nodes',
              Icons.hub_rounded,
              const Color(0xFF4D8DFF),
            ),
          ),

          const SizedBox(width: 12),

          Expanded(
            child: _metricCard(
              'TRANSACTIONS',
              '$transactions',
              Icons.swap_horiz_rounded,
              const Color(0xFFB36BFF),
            ),
          ),

          const SizedBox(width: 12),

          Expanded(
            child: _metricCard(
              'HIGH RISK',
              '$highRisk',
              Icons.warning_amber_rounded,
              const Color(0xFFFF4D5A),
            ),
          ),

          const SizedBox(width: 12),

          Expanded(
            child: _metricCard(
              'MULE ACCOUNTS',
              '$mules',
              Icons.person_search_rounded,
              const Color(0xFFFFB020),
            ),
          ),

          const SizedBox(width: 12),

          Expanded(
            child: _metricCard(
              'NETWORK VOLUME',
              _formatAmount(volume),
              Icons.currency_rupee_rounded,
              const Color(0xFF2DD4BF),
            ),
          ),
        ],
      ),
    );
  }

  Widget _metricCard(
    String label,
    String value,
    IconData icon,
    Color color,
  ) {
    return Container(
      height: 78,

      padding: const EdgeInsets.symmetric(
        horizontal: 16,
        vertical: 12,
      ),

      decoration: BoxDecoration(
        color: const Color(0xFF111A2E),
        borderRadius: BorderRadius.circular(12),

        border: Border.all(
          color: color.withValues(alpha: 0.25),
        ),
      ),

      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),

            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(9),
            ),

            child: Icon(
              icon,
              size: 19,
              color: color,
            ),
          ),

          const SizedBox(width: 11),

          Expanded(
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,

              mainAxisAlignment:
                  MainAxisAlignment.center,

              children: [
                Text(
                  value,
                  overflow: TextOverflow.ellipsis,

                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 19,
                    fontWeight: FontWeight.w700,
                  ),
                ),

                const SizedBox(height: 3),

                Text(
                  label,
                  overflow: TextOverflow.ellipsis,

                  style: const TextStyle(
                    color: Color(0xFF8994A8),
                    fontSize: 9,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.7,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // FILTER TOOLBAR
  // ============================================================

  Widget _buildToolbar({
    required int visibleCount,
    required int totalCount,
  }) {
    final filters = [
      (
        'ALL',
        'All Accounts',
        Icons.hub_rounded,
      ),
      (
        'HIGH',
        'High Risk',
        Icons.warning_rounded,
      ),
      (
        'MULE',
        'Mule',
        Icons.person_search_rounded,
      ),
      (
        'OUT',
        'Outbound',
        Icons.call_made_rounded,
      ),
    ];

    return Padding(
      padding: const EdgeInsets.fromLTRB(
        16,
        0,
        16,
        12,
      ),

      child: Row(
        children: [
          const Text(
            'NETWORK FILTER',

            style: TextStyle(
              color: Color(0xFF7F8BA0),
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 1,
            ),
          ),

          const SizedBox(width: 12),

          ...filters.map(
            (item) => Padding(
              padding: const EdgeInsets.only(
                right: 8,
              ),

              child: _filterChip(
                item.$1,
                item.$2,
                item.$3,
              ),
            ),
          ),

          const Spacer(),

          Text(
            '$visibleCount / $totalCount',
            style: const TextStyle(
              color: Color(0xFF66738A),
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),

          const SizedBox(width: 10),

          const Icon(
            Icons.touch_app_rounded,
            color: Color(0xFF66738A),
            size: 15,
          ),

          const SizedBox(width: 5),

          const Text(
            'Click a node to investigate',
            style: TextStyle(
              color: Color(0xFF66738A),
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }

  Widget _filterChip(
    String value,
    String label,
    IconData icon,
  ) {
    final bool selected = _filter == value;

    return InkWell(
      borderRadius: BorderRadius.circular(20),

      onTap: () {
        setState(() {
          _filter = value;
          _selectedNodeId = null;
        });

        // Important:
        // reset viewport when switching filters.
        WidgetsBinding.instance.addPostFrameCallback((_) {
          _controller.resetView();
        });
      },

      child: AnimatedContainer(
        duration: const Duration(
          milliseconds: 180,
        ),

        padding: const EdgeInsets.symmetric(
          horizontal: 12,
          vertical: 7,
        ),

        decoration: BoxDecoration(
          color: selected
              ? const Color(0xFF4D8DFF)
                  .withValues(alpha: 0.14)
              : const Color(0xFF111A2E),

          borderRadius: BorderRadius.circular(20),

          border: Border.all(
            color: selected
                ? const Color(0xFF4D8DFF)
                : const Color(0xFF26324A),
          ),
        ),

        child: Row(
          mainAxisSize: MainAxisSize.min,

          children: [
            Icon(
              icon,
              size: 14,

              color: selected
                  ? const Color(0xFF6EA3FF)
                  : const Color(0xFF7F8BA0),
            ),

            const SizedBox(width: 6),

            Text(
              label,

              style: TextStyle(
                color: selected
                    ? Colors.white
                    : const Color(0xFF8C97AA),

                fontSize: 11,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // GRAPH
  // ============================================================

  Widget _buildGraph(
    List<NetworkNode> nodes,
    List<NetworkEdge> edges,
  ) {
    final graph = Graph();

    final nodeMap = <String, Node>{};

    for (final item in nodes) {
      final graphNode = Node.Id(item.id);

      graph.addNode(graphNode);

      nodeMap[item.id] = graphNode;
    }

    for (final edge in edges) {
      final sourceNode = nodeMap[edge.source];
      final targetNode = nodeMap[edge.target];

      if (sourceNode != null &&
          targetNode != null) {
        graph.addEdge(
          sourceNode,
          targetNode,
          paint: Paint()
            ..color = const Color(0xFF53627D)
            ..strokeWidth = 1.5,
        );
      }
    }

    final config =
        FruchtermanReingoldConfiguration(
      iterations: 100,
      repulsionRate: 0.8,
      attractionRate: 0.8,
      clusterPadding: 30,
      shuffleNodes: true,
    );

    final algorithm =
        FruchtermanReingoldAlgorithm(
      config,
      renderer: ArrowEdgeRenderer(),
    );

    final nodeData = <String, NetworkNode>{
      for (final node in nodes) node.id: node,
    };

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0D1527),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: const Color(0xFF202C43),
        ),
      ),

      clipBehavior: Clip.antiAlias,

      child: Stack(
        children: [
          Positioned.fill(
            child: CustomPaint(
              painter: _GridPainter(),
            ),
          ),

          Positioned(
            left: 18,
            top: 16,
            child: _graphLabel(
              Icons.account_tree_rounded,
              'LIVE NETWORK TOPOLOGY',
            ),
          ),

          Positioned(
            right: 18,
            top: 14,
            child: _buildLegend(),
          ),

          if (nodes.isEmpty)
            const Center(
              child: Text(
                'No accounts match this filter',
                style: TextStyle(
                  color: Color(0xFF7F8BA0),
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            )
          else
            Positioned.fill(
              child: Padding(
                padding: const EdgeInsets.only(
                  top: 55,
                  bottom: 40,
                  left: 20,
                  right: 20,
                ),

                child: GraphView.builder(
                  graph: graph,
                  algorithm: algorithm,
                  controller: _controller,

                  // VERY IMPORTANT:
                  // filtered graphs must fit into viewport.
                  autoZoomToFit: true,

                  centerGraph: true,

                  animated: false,

                  builder: (Node node) {
                    final id =
                        node.key!.value.toString();

                    final data = nodeData[id];

                    if (data == null) {
                      return const SizedBox.shrink();
                    }

                    return _networkNode(
                      data,
                      selected:
                          _selectedNodeId == id,
                    );
                  },
                ),
              ),
            ),

          Positioned(
            left: 18,
            bottom: 16,
            child: Row(
              children: [
                _controlHint(
                  Icons.zoom_in_rounded,
                  'Scroll to zoom',
                ),

                const SizedBox(width: 12),

                _controlHint(
                  Icons.pan_tool_rounded,
                  'Drag to pan',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // LEGEND
  // ============================================================

  Widget _buildLegend() {
    return Column(
      crossAxisAlignment:
          CrossAxisAlignment.end,

      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            _legendDot(
              const Color(0xFFFFB020),
              'Mule',
            ),

            const SizedBox(width: 12),

            _legendDot(
              const Color(0xFF9B7BFF),
              'Structured',
            ),

            const SizedBox(width: 12),

            _legendDot(
              const Color(0xFF4D8DFF),
              'Outbound',
            ),

            const SizedBox(width: 12),

            _legendDot(
              const Color(0xFF94A3B8),
              'Other',
            ),
          ],
        ),

        const SizedBox(height: 8),

        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            _legendDot(
              const Color(0xFFFF4D5A),
              'High',
            ),

            const SizedBox(width: 12),

            _legendDot(
              const Color(0xFFFFB020),
              'Uncertain',
            ),

            const SizedBox(width: 12),

            _legendDot(
              const Color(0xFF2DD4BF),
              'Low',
            ),
          ],
        ),
      ],
    );
  }

  // ============================================================
  // NETWORK NODE
  // ============================================================

  Widget _networkNode(
    NetworkNode data, {
    required bool selected,
  }) {
    final id = data.id;

    final type = _nodeType(id);

    // Node colour = ACCOUNT TYPE
    final typeColor = _typeColor(id);

    // Risk colour = RISK
    final risk = _calculatedRisk(data);
    final riskColor = _riskColor(risk);

    final score = data.riskScore;

    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedNodeId = id;
        });
      },

      child: AnimatedContainer(
        duration: const Duration(
          milliseconds: 180,
        ),

        width: selected ? 94 : 76,
        height: selected ? 94 : 76,

        decoration: BoxDecoration(
          shape: BoxShape.circle,

          color: const Color(0xFF111A2E),

          // IMPORTANT:
          // Border is now TYPE color,
          // NOT risk color.
          border: Border.all(
            color: selected
                ? Colors.white
                : typeColor,

            width: selected ? 3 : 2,
          ),

          boxShadow: [
            BoxShadow(
              color: typeColor.withValues(
                alpha: selected
                    ? 0.40
                    : 0.20,
              ),

              blurRadius:
                  selected ? 18 : 10,

              spreadRadius:
                  selected ? 3 : 1,
            ),
          ],
        ),

        child: Stack(
          alignment: Alignment.center,

          children: [
            Column(
              mainAxisAlignment:
                  MainAxisAlignment.center,

              children: [
                Icon(
                  _nodeIcon(type),
                  color: typeColor,
                  size: selected ? 21 : 17,
                ),

                const SizedBox(height: 2),

                Text(
                  type,
                  style: TextStyle(
                    color: Colors.white,
                    fontSize:
                        selected ? 9 : 7,
                    fontWeight:
                        FontWeight.w700,
                  ),
                ),

                const SizedBox(height: 1),

                Text(
                  '${score.toStringAsFixed(0)}%',
                  style: TextStyle(
                    color: riskColor,
                    fontSize:
                        selected ? 11 : 9,
                    fontWeight:
                        FontWeight.w800,
                  ),
                ),
              ],
            ),

            // Risk indicator
            Positioned(
              right: selected ? 11 : 8,
              top: selected ? 11 : 8,

              child: Container(
                width: 9,
                height: 9,

                decoration: BoxDecoration(
                  color: riskColor,
                  shape: BoxShape.circle,

                  border: Border.all(
                    color:
                        const Color(0xFF111A2E),
                    width: 1.5,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // SELECTED ACCOUNT PANEL
  // ============================================================

  Widget _buildSelectedPanel(
    List<NetworkNode> nodes,
    List<NetworkEdge> edges,
  ) {
    final node = nodes.firstWhere(
      (item) => item.id == _selectedNodeId,

      orElse: () => NetworkNode(
        id: '',
        riskScore: 0,
        riskLevel: 'UNKNOWN',
        label: 0,
      ),
    );

    if (node.id.isEmpty) {
      return const SizedBox.shrink();
    }

    final id = node.id;

    final risk = _calculatedRisk(node);

    final score = node.riskScore;

    final outgoing = edges
        .where(
          (edge) => edge.source == id,
        )
        .toList();

    final incoming = edges
        .where(
          (edge) => edge.target == id,
        )
        .toList();

    double outgoingAmount = 0;
    double incomingAmount = 0;

    for (final edge in outgoing) {
      outgoingAmount += edge.amount;
    }

    for (final edge in incoming) {
      incomingAmount += edge.amount;
    }

    final riskColor = _riskColor(risk);

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF10192B),

        borderRadius:
            BorderRadius.circular(16),

        border: Border.all(
          color: const Color(0xFF25334D),
        ),
      ),

      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,

        children: [
          Padding(
            padding:
                const EdgeInsets.all(18),

            child: Row(
              children: [
                Container(
                  padding:
                      const EdgeInsets.all(11),

                  decoration: BoxDecoration(
                    color: _typeColor(id)
                        .withValues(alpha: 0.12),

                    shape: BoxShape.circle,
                  ),

                  child: Icon(
                    _nodeIcon(
                      _nodeType(id),
                    ),

                    color: _typeColor(id),

                    size: 21,
                  ),
                ),

                const SizedBox(width: 11),

                Expanded(
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,

                    children: [
                      const Text(
                        'ACCOUNT INVESTIGATION',

                        style: TextStyle(
                          color:
                              Color(0xFF748198),

                          fontSize: 9,

                          fontWeight:
                              FontWeight.w700,

                          letterSpacing: 1,
                        ),
                      ),

                      const SizedBox(height: 4),

                      Text(
                        _shortId(id),

                        style:
                            const TextStyle(
                          color: Colors.white,

                          fontSize: 14,

                          fontWeight:
                              FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),

                IconButton(
                  onPressed: () {
                    setState(() {
                      _selectedNodeId = null;
                    });
                  },

                  icon: const Icon(
                    Icons.close_rounded,
                    size: 18,
                  ),

                  color:
                      const Color(0xFF77849A),
                ),
              ],
            ),
          ),

          const Divider(
            height: 1,
            color: Color(0xFF25334D),
          ),

          Expanded(
            child: SingleChildScrollView(
              padding:
                  const EdgeInsets.all(18),

              child: Column(
                crossAxisAlignment:
                    CrossAxisAlignment.start,

                children: [
                  _riskScoreCard(
                    score,
                    risk,
                    riskColor,
                  ),

                  const SizedBox(height: 16),

                  _infoRow(
                    'ACCOUNT TYPE',
                    _nodeType(id),
                  ),

                  const SizedBox(height: 12),

                  _infoRow(
                    'OUTGOING TRANSACTIONS',
                    '${outgoing.length}',
                  ),

                  const SizedBox(height: 12),

                  _infoRow(
                    'INCOMING TRANSACTIONS',
                    '${incoming.length}',
                  ),

                  const SizedBox(height: 12),

                  _infoRow(
                    'OUTGOING VOLUME',
                    _formatAmount(
                      outgoingAmount,
                    ),
                  ),

                  const SizedBox(height: 12),

                  _infoRow(
                    'INCOMING VOLUME',
                    _formatAmount(
                      incomingAmount,
                    ),
                  ),

                  const SizedBox(height: 18),

                  const Text(
                    'NETWORK CONNECTIONS',

                    style: TextStyle(
                      color: Color(0xFF748198),
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1,
                    ),
                  ),

                  const SizedBox(height: 9),

                  ...outgoing.take(4).map(
                    (edge) => _connectionRow(
                      Icons.call_made_rounded,
                      edge.target,
                      edge.amount,
                      const Color(0xFFFFB020),
                    ),
                  ),

                  ...incoming.take(4).map(
                    (edge) => _connectionRow(
                      Icons.call_received_rounded,
                      edge.source,
                      edge.amount,
                      const Color(0xFF4D8DFF),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // RISK CARD
  // ============================================================

    Widget _riskScoreCard(double score, String risk, Color color) {
    final double progress = (score / 100).clamp(0.0, 1.0);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.20)),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 54,
            height: 54,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CircularProgressIndicator(
                  value: progress,
                  strokeWidth: 5,
                  backgroundColor: const Color(0xFF26324A),
                  valueColor: AlwaysStoppedAnimation<Color>(color),
                ),
                Text(
                  score.toStringAsFixed(0),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 14),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'ML RISK SCORE',
                style: TextStyle(
                  color: Color(0xFF748198),
                  fontSize: 9,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.8,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                risk,
                style: TextStyle(
                  color: color,
                  fontSize: 17,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ============================================================
  // INFO ROW
  // ============================================================

  Widget _infoRow(
    String label,
    String value,
  ) {
    return Row(
      children: [
        Expanded(
          child: Text(
            label,

            style: const TextStyle(
              color: Color(0xFF748198),
              fontSize: 10,
            ),
          ),
        ),

        Text(
          value,

          style: const TextStyle(
            color: Colors.white,

            fontSize: 11,

            fontWeight:
                FontWeight.w700,
          ),
        ),
      ],
    );
  }

  // ============================================================
  // CONNECTION
  // ============================================================

  Widget _connectionRow(
    IconData icon,
    String id,
    double amount,
    Color color,
  ) {
    return Container(
      margin:
          const EdgeInsets.only(
        bottom: 7,
      ),

      padding:
          const EdgeInsets.symmetric(
        horizontal: 9,
        vertical: 8,
      ),

      decoration: BoxDecoration(
        color: const Color(
          0xFF0B1324,
        ),

        borderRadius:
            BorderRadius.circular(8),
      ),

      child: Row(
        children: [
          Icon(
            icon,
            size: 13,
            color: color,
          ),

          const SizedBox(width: 7),

          Expanded(
            child: Text(
              _shortId(id),

              style: const TextStyle(
                color:
                    Color(0xFFB8C2D2),

                fontSize: 10,
              ),
            ),
          ),

          Text(
            _formatAmount(amount),

            style: const TextStyle(
              color: Colors.white,

              fontSize: 10,

              fontWeight:
                  FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // LABEL
  // ============================================================

  Widget _graphLabel(
    IconData icon,
    String text,
  ) {
    return Container(
      padding:
          const EdgeInsets.symmetric(
        horizontal: 10,
        vertical: 7,
      ),

      decoration: BoxDecoration(
        color: const Color(
          0xFF111A2E,
        ),

        borderRadius:
            BorderRadius.circular(8),

        border: Border.all(
          color: const Color(
            0xFF26324A,
          ),
        ),
      ),

      child: Row(
        children: [
          Icon(
            icon,

            color:
                const Color(0xFF4D8DFF),

            size: 14,
          ),

          const SizedBox(width: 7),

          Text(
            text,

            style: const TextStyle(
              color:
                  Color(0xFF9BA7BA),

              fontSize: 9,

              fontWeight:
                  FontWeight.w700,

              letterSpacing: 0.8,
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // LEGEND DOT
  // ============================================================

  Widget _legendDot(
    Color color,
    String label,
  ) {
    return Row(
      children: [
        Container(
          width: 7,
          height: 7,

          decoration:
              BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),

        const SizedBox(width: 5),

        Text(
          label,

          style: const TextStyle(
            color:
                Color(0xFF8490A4),

            fontSize: 9,
          ),
        ),
      ],
    );
  }

  // ============================================================
  // CONTROL HINT
  // ============================================================

  Widget _controlHint(
    IconData icon,
    String text,
  ) {
    return Row(
      children: [
        Icon(
          icon,

          size: 13,

          color:
              const Color(0xFF59667D),
        ),

        const SizedBox(width: 5),

        Text(
          text,

          style: const TextStyle(
            color:
                Color(0xFF59667D),

            fontSize: 9,
          ),
        ),
      ],
    );
  }

  // ============================================================
  // ERROR
  // ============================================================

  Widget _buildError(
    String error,
  ) {
    return Center(
      child: Container(
        margin:
            const EdgeInsets.all(30),

        padding:
            const EdgeInsets.all(24),

        decoration: BoxDecoration(
          color: const Color(
            0xFF111A2E,
          ),

          borderRadius:
              BorderRadius.circular(16),

          border: Border.all(
            color:
                const Color(0xFFFF4D5A)
                    .withValues(
              alpha: 0.25,
            ),
          ),
        ),

        child: Column(
          mainAxisSize:
              MainAxisSize.min,

          children: [
            const Icon(
              Icons.cloud_off_rounded,

              color:
                  Color(0xFFFF4D5A),

              size: 40,
            ),

            const SizedBox(height: 12),

            const Text(
              'Network service unavailable',

              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight:
                    FontWeight.w700,
              ),
            ),

            const SizedBox(height: 8),

            Text(
              error,

              textAlign:
                  TextAlign.center,

              style: const TextStyle(
                color:
                    Color(0xFF8C97AA),

                fontSize: 11,
              ),
            ),

            const SizedBox(height: 16),

            ElevatedButton.icon(
              onPressed: _refresh,

              icon: const Icon(
                Icons.refresh_rounded,
              ),

              label:
                  const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}

// ================================================================
// GRID PAINTER
// ================================================================

class _GridPainter
    extends CustomPainter {
  @override
  void paint(
    Canvas canvas,
    Size size,
  ) {
    final Paint paint = Paint()
      ..color =
          const Color(0xFF162138)
      ..strokeWidth = 0.5;

    const double spacing = 40.0;

    for (
      double x = 0;
      x < size.width;
      x += spacing
    ) {
      canvas.drawLine(
        Offset(x, 0),
        Offset(x, size.height),
        paint,
      );
    }

    for (
      double y = 0;
      y < size.height;
      y += spacing
    ) {
      canvas.drawLine(
        Offset(0, y),
        Offset(size.width, y),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(
    covariant CustomPainter oldDelegate,
  ) {
    return false;
  }
}