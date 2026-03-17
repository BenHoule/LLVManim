; ModuleID = 'double.c'
source_filename = "double.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

; Function Attrs: noinline nounwind optnone uwtable
define dso_local void @init(ptr noundef %p) #0 !dbg !13 {
entry:
  %p.addr = alloca ptr, align 8
  store ptr %p, ptr %p.addr, align 8
  call void @llvm.dbg.declare(metadata ptr %p.addr, metadata !17, metadata !DIExpression()), !dbg !18
  %0 = load ptr, ptr %p.addr, align 8, !dbg !19
  store i32 1, ptr %0, align 4, !dbg !20
  ret void, !dbg !21
}

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare void @llvm.dbg.declare(metadata, metadata, metadata) #1

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @double_1(ptr noundef %p) #0 !dbg !22 {
entry:
  %p.addr = alloca ptr, align 8
  %tmp = alloca i32, align 4
  store ptr %p, ptr %p.addr, align 8
  call void @llvm.dbg.declare(metadata ptr %p.addr, metadata !25, metadata !DIExpression()), !dbg !26
  call void @llvm.dbg.declare(metadata ptr %tmp, metadata !27, metadata !DIExpression()), !dbg !28
  %0 = load ptr, ptr %p.addr, align 8, !dbg !29
  %1 = load i32, ptr %0, align 4, !dbg !30
  store i32 %1, ptr %tmp, align 4, !dbg !28
  %2 = load i32, ptr %tmp, align 4, !dbg !31
  %mul = mul nsw i32 2, %2, !dbg !32
  %3 = load ptr, ptr %p.addr, align 8, !dbg !33
  store i32 %mul, ptr %3, align 4, !dbg !34
  %4 = load ptr, ptr %p.addr, align 8, !dbg !35
  %5 = load i32, ptr %4, align 4, !dbg !36
  ret i32 %5, !dbg !37
}

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @main() #0 !dbg !38 {
entry:
  %retval = alloca i32, align 4
  %r = alloca i32, align 4
  %p = alloca ptr, align 8
  store i32 0, ptr %retval, align 4
  call void @llvm.dbg.declare(metadata ptr %r, metadata !41, metadata !DIExpression()), !dbg !42
  store i32 0, ptr %r, align 4, !dbg !42
  call void @llvm.dbg.declare(metadata ptr %p, metadata !43, metadata !DIExpression()), !dbg !44
  %call = call noalias ptr @malloc(i64 noundef 4) #3, !dbg !45
  store ptr %call, ptr %p, align 8, !dbg !44
  %0 = load ptr, ptr %p, align 8, !dbg !46
  call void @init(ptr noundef %0), !dbg !47
  br label %while.cond, !dbg !48

while.cond:                                       ; preds = %while.body, %entry
  %1 = load ptr, ptr %p, align 8, !dbg !49
  %2 = load i32, ptr %1, align 4, !dbg !50
  %cmp = icmp slt i32 %2, 100, !dbg !51
  br i1 %cmp, label %while.body, label %while.end, !dbg !48

while.body:                                       ; preds = %while.cond
  %3 = load ptr, ptr %p, align 8, !dbg !52
  %call1 = call i32 @double_1(ptr noundef %3), !dbg !54
  store i32 %call1, ptr %r, align 4, !dbg !55
  br label %while.cond, !dbg !48, !llvm.loop !56

while.end:                                        ; preds = %while.cond
  %4 = load i32, ptr %r, align 4, !dbg !59
  ret i32 %4, !dbg !60
}

; Function Attrs: nounwind allocsize(0)
declare noalias ptr @malloc(i64 noundef) #2

attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }
attributes #2 = { nounwind allocsize(0) "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { nounwind allocsize(0) }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!5, !6, !7, !8, !9, !10, !11}
!llvm.ident = !{!12}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "Ubuntu clang version 18.1.3 (1ubuntu1)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, retainedTypes: !2, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "double.c", directory: "/home/benh/LLVManim", checksumkind: CSK_MD5, checksum: "0f941b637837176c30f52c4a0313c1b1")
!2 = !{!3}
!3 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !4, size: 64)
!4 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!5 = !{i32 7, !"Dwarf Version", i32 5}
!6 = !{i32 2, !"Debug Info Version", i32 3}
!7 = !{i32 1, !"wchar_size", i32 4}
!8 = !{i32 8, !"PIC Level", i32 2}
!9 = !{i32 7, !"PIE Level", i32 2}
!10 = !{i32 7, !"uwtable", i32 2}
!11 = !{i32 7, !"frame-pointer", i32 2}
!12 = !{!"Ubuntu clang version 18.1.3 (1ubuntu1)"}
!13 = distinct !DISubprogram(name: "init", scope: !1, file: !1, line: 5, type: !14, scopeLine: 5, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !16)
!14 = !DISubroutineType(types: !15)
!15 = !{null, !3}
!16 = !{}
!17 = !DILocalVariable(name: "p", arg: 1, scope: !13, file: !1, line: 5, type: !3)
!18 = !DILocation(line: 5, column: 16, scope: !13)
!19 = !DILocation(line: 6, column: 4, scope: !13)
!20 = !DILocation(line: 6, column: 5, scope: !13)
!21 = !DILocation(line: 7, column: 1, scope: !13)
!22 = distinct !DISubprogram(name: "double_1", scope: !1, file: !1, line: 9, type: !23, scopeLine: 9, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !16)
!23 = !DISubroutineType(types: !24)
!24 = !{!4, !3}
!25 = !DILocalVariable(name: "p", arg: 1, scope: !22, file: !1, line: 9, type: !3)
!26 = !DILocation(line: 9, column: 19, scope: !22)
!27 = !DILocalVariable(name: "tmp", scope: !22, file: !1, line: 10, type: !4)
!28 = !DILocation(line: 10, column: 7, scope: !22)
!29 = !DILocation(line: 10, column: 14, scope: !22)
!30 = !DILocation(line: 10, column: 13, scope: !22)
!31 = !DILocation(line: 11, column: 10, scope: !22)
!32 = !DILocation(line: 11, column: 9, scope: !22)
!33 = !DILocation(line: 11, column: 4, scope: !22)
!34 = !DILocation(line: 11, column: 6, scope: !22)
!35 = !DILocation(line: 12, column: 12, scope: !22)
!36 = !DILocation(line: 12, column: 11, scope: !22)
!37 = !DILocation(line: 12, column: 3, scope: !22)
!38 = distinct !DISubprogram(name: "main", scope: !1, file: !1, line: 15, type: !39, scopeLine: 15, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !16)
!39 = !DISubroutineType(types: !40)
!40 = !{!4}
!41 = !DILocalVariable(name: "r", scope: !38, file: !1, line: 16, type: !4)
!42 = !DILocation(line: 16, column: 7, scope: !38)
!43 = !DILocalVariable(name: "p", scope: !38, file: !1, line: 17, type: !3)
!44 = !DILocation(line: 17, column: 8, scope: !38)
!45 = !DILocation(line: 17, column: 20, scope: !38)
!46 = !DILocation(line: 18, column: 8, scope: !38)
!47 = !DILocation(line: 18, column: 3, scope: !38)
!48 = !DILocation(line: 19, column: 3, scope: !38)
!49 = !DILocation(line: 19, column: 11, scope: !38)
!50 = !DILocation(line: 19, column: 10, scope: !38)
!51 = !DILocation(line: 19, column: 13, scope: !38)
!52 = !DILocation(line: 20, column: 18, scope: !53)
!53 = distinct !DILexicalBlock(scope: !38, file: !1, line: 19, column: 20)
!54 = !DILocation(line: 20, column: 9, scope: !53)
!55 = !DILocation(line: 20, column: 7, scope: !53)
!56 = distinct !{!56, !48, !57, !58}
!57 = !DILocation(line: 21, column: 3, scope: !38)
!58 = !{!"llvm.loop.mustprogress"}
!59 = !DILocation(line: 22, column: 10, scope: !38)
!60 = !DILocation(line: 22, column: 3, scope: !38)
