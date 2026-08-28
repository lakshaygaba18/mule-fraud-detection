import 'package:flutter/material.dart';

import 'screens/dashboard_screen.dart';

void main() {
  runApp(const FraudDashboardApp());
}

class FraudDashboardApp extends StatelessWidget {
  const FraudDashboardApp({super.key});

  @override
  Widget build(BuildContext context) {
    const backgroundColor = Color(0xFF090E1D);
    const surfaceColor = Color(0xFF111A2E);
    const primaryColor = Color(0xFF4D8DFF);

    return MaterialApp(
      title: 'Fraud Intelligence Dashboard',
      debugShowCheckedModeBanner: false,

      theme: ThemeData(
        useMaterial3: true,

        brightness: Brightness.dark,

        scaffoldBackgroundColor: backgroundColor,

        colorScheme: const ColorScheme.dark(
          primary: primaryColor,
          surface: surfaceColor,

          // Risk / status colors
          error: Color(0xFFFF4D5A),
          tertiary: Color(0xFF2DD4BF),
        ),

        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0E1628),
          foregroundColor: Colors.white,
          elevation: 0,

          centerTitle: false,

          titleTextStyle: TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.w700,
          ),

          iconTheme: IconThemeData(
            color: Color(0xFFB8C2D2),
          ),
        ),

        cardTheme: CardThemeData(
          color: surfaceColor,
          elevation: 0,

          margin: EdgeInsets.zero,

          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(
              Radius.circular(14),
            ),
            side: BorderSide(
              color: Color(0xFF26324A),
              width: 1,
            ),
          ),
        ),

        dividerTheme: const DividerThemeData(
          color: Color(0xFF25334D),
          thickness: 1,
          space: 1,
        ),

        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: const Color(0xFF111A2E),

          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),

            borderSide: const BorderSide(
              color: Color(0xFF26324A),
            ),
          ),

          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),

            borderSide: const BorderSide(
              color: Color(0xFF26324A),
            ),
          ),

          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),

            borderSide: const BorderSide(
              color: primaryColor,
              width: 1.5,
            ),
          ),

          labelStyle: const TextStyle(
            color: Color(0xFF8994A8),
          ),

          hintStyle: const TextStyle(
            color: Color(0xFF66738A),
          ),
        ),

        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: primaryColor,
            foregroundColor: Colors.white,

            elevation: 0,

            padding: const EdgeInsets.symmetric(
              horizontal: 18,
              vertical: 13,
            ),

            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(9),
            ),

            textStyle: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),

        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: const Color(0xFFB8C2D2),

            side: const BorderSide(
              color: Color(0xFF26324A),
            ),

            padding: const EdgeInsets.symmetric(
              horizontal: 16,
              vertical: 12,
            ),

            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(9),
            ),
          ),
        ),

        textButtonTheme: TextButtonThemeData(
          style: TextButton.styleFrom(
            foregroundColor: primaryColor,

            textStyle: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),

        iconButtonTheme: IconButtonThemeData(
          style: IconButton.styleFrom(
            foregroundColor: const Color(0xFF9BA7BA),

            hoverColor: primaryColor.withValues(
              alpha: 0.08,
            ),

            highlightColor: primaryColor.withValues(
              alpha: 0.12,
            ),
          ),
        ),

        tooltipTheme: TooltipThemeData(
          decoration: BoxDecoration(
            color: const Color(0xFF182238),
            borderRadius: BorderRadius.circular(7),
            border: Border.all(
              color: const Color(0xFF26324A),
            ),
          ),

          textStyle: const TextStyle(
            color: Colors.white,
            fontSize: 11,
          ),
        ),

        progressIndicatorTheme:
            const ProgressIndicatorThemeData(
          color: primaryColor,
          linearTrackColor: Color(0xFF26324A),
        ),

        snackBarTheme: SnackBarThemeData(
          backgroundColor: const Color(0xFF182238),

          contentTextStyle: const TextStyle(
            color: Colors.white,
            fontSize: 12,
          ),

          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),

          behavior: SnackBarBehavior.floating,
        ),

        scrollbarTheme: ScrollbarThemeData(
          thumbColor: WidgetStateProperty.all(
            const Color(0xFF35445F),
          ),

          radius: const Radius.circular(10),

          thickness: WidgetStateProperty.all(6),
        ),
      ),

      home: const DashboardScreen(),
    );
  }
}