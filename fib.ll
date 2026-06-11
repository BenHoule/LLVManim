; ModuleID = 'fib.c'
source_filename = "fib.c"
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
define dso_local i32 @fib(ptr noundef %p) #0 !dbg !22 {
entry:
  %retval = alloca i32, align 4
  %p.addr = alloca ptr, align 8
  %tmp = alloca ptr, align 8
  store ptr %p, ptr %p.addr, align 8
  call void @llvm.dbg.declare(metadata ptr %p.addr, metadata !25, metadata !DIExpression()), !dbg !26
  %0 = load ptr, ptr %p.addr, align 8, !dbg !27
  %1 = load i32, ptr %0, align 4, !dbg !29
  %cmp = icmp sgt i32 %1, 2, !dbg !30
  br i1 %cmp, label %if.then, label %if.end, !dbg !31

if.then:                                          ; preds = %entry
  call void @llvm.dbg.declare(metadata ptr %tmp, metadata !32, metadata !DIExpression()), !dbg !34
  %call = call noalias ptr @malloc(i64 noundef 8) #4, !dbg !35
  store ptr %call, ptr %tmp, align 8, !dbg !34
  %2 = load ptr, ptr %p.addr, align 8, !dbg !36
  %3 = load i32, ptr %2, align 4, !dbg !37
  %sub = sub nsw i32 %3, 1, !dbg !38
  %4 = load ptr, ptr %tmp, align 8, !dbg !39
  %arrayidx = getelementptr inbounds i32, ptr %4, i64 0, !dbg !39
  store i32 %sub, ptr %arrayidx, align 4, !dbg !40
  %5 = load ptr, ptr %p.addr, align 8, !dbg !41
  %6 = load i32, ptr %5, align 4, !dbg !42
  %sub1 = sub nsw i32 %6, 2, !dbg !43
  %7 = load ptr, ptr %tmp, align 8, !dbg !44
  %arrayidx2 = getelementptr inbounds i32, ptr %7, i64 1, !dbg !44
  store i32 %sub1, ptr %arrayidx2, align 4, !dbg !45
  %8 = load ptr, ptr %tmp, align 8, !dbg !46
  %call3 = call i32 @fib(ptr noundef %8), !dbg !47
  %9 = load ptr, ptr %tmp, align 8, !dbg !48
  %arrayidx4 = getelementptr inbounds i32, ptr %9, i64 1, !dbg !48
  %call5 = call i32 @fib(ptr noundef %arrayidx4), !dbg !49
  %add = add nsw i32 %call3, %call5, !dbg !50
  %10 = load ptr, ptr %p.addr, align 8, !dbg !51
  store i32 %add, ptr %10, align 4, !dbg !52
  %11 = load ptr, ptr %tmp, align 8, !dbg !53
  call void @free(ptr noundef %11) #5, !dbg !54
  %12 = load ptr, ptr %p.addr, align 8, !dbg !55
  %13 = load i32, ptr %12, align 4, !dbg !56
  store i32 %13, ptr %retval, align 4, !dbg !57
  br label %return, !dbg !57

if.end:                                           ; preds = %entry
  %14 = load ptr, ptr %p.addr, align 8, !dbg !58
  %15 = load i32, ptr %14, align 4, !dbg !59
  %cmp6 = icmp sgt i32 %15, 0, !dbg !60
  %16 = zext i1 %cmp6 to i64, !dbg !59
  %cond = select i1 %cmp6, i32 1, i32 0, !dbg !59
  store i32 %cond, ptr %retval, align 4, !dbg !61
  br label %return, !dbg !61

return:                                           ; preds = %if.end, %if.then
  %17 = load i32, ptr %retval, align 4, !dbg !62
  ret i32 %17, !dbg !62
}

; Function Attrs: nounwind allocsize(0)
declare noalias ptr @malloc(i64 noundef) #2

; Function Attrs: nounwind
declare void @free(ptr noundef) #3

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @main() #0 !dbg !63 {
entry:
  %retval = alloca i32, align 4
  %r = alloca i32, align 4
  %p = alloca ptr, align 8
  store i32 0, ptr %retval, align 4
  call void @llvm.dbg.declare(metadata ptr %r, metadata !66, metadata !DIExpression()), !dbg !67
  store i32 0, ptr %r, align 4, !dbg !67
  call void @llvm.dbg.declare(metadata ptr %p, metadata !68, metadata !DIExpression()), !dbg !69
  %call = call noalias ptr @malloc(i64 noundef 4) #4, !dbg !70
  store ptr %call, ptr %p, align 8, !dbg !69
  %0 = load ptr, ptr %p, align 8, !dbg !71
  call void @init(ptr noundef %0), !dbg !72
  %1 = load ptr, ptr %p, align 8, !dbg !73
  %call1 = call i32 @fib(ptr noundef %1), !dbg !74
  store i32 %call1, ptr %r, align 4, !dbg !75
  %2 = load ptr, ptr %p, align 8, !dbg !76
  call void @free(ptr noundef %2) #5, !dbg !77
  %3 = load i32, ptr %r, align 4, !dbg !78
  ret i32 %3, !dbg !79
}

attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }
attributes #2 = { nounwind allocsize(0) "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #4 = { nounwind allocsize(0) }
attributes #5 = { nounwind }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!5, !6, !7, !8, !9, !10, !11}
!llvm.ident = !{!12}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "Ubuntu clang version 18.1.3 (1ubuntu1)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, retainedTypes: !2, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "fib.c", directory: "/home/bhoule/LLVManim", checksumkind: CSK_MD5, checksum: "342c516b3f456b2054c0b712c9f14ae6")
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
!13 = distinct !DISubprogram(name: "init", scope: !1, file: !1, line: 3, type: !14, scopeLine: 3, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !16)
!14 = !DISubroutineType(types: !15)
!15 = !{null, !3}
!16 = !{}
!17 = !DILocalVariable(name: "p", arg: 1, scope: !13, file: !1, line: 3, type: !3)
!18 = !DILocation(line: 3, column: 16, scope: !13)
!19 = !DILocation(line: 4, column: 4, scope: !13)
!20 = !DILocation(line: 4, column: 6, scope: !13)
!21 = !DILocation(line: 5, column: 1, scope: !13)
!22 = distinct !DISubprogram(name: "fib", scope: !1, file: !1, line: 7, type: !23, scopeLine: 7, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !16)
!23 = !DISubroutineType(types: !24)
!24 = !{!4, !3}
!25 = !DILocalVariable(name: "p", arg: 1, scope: !22, file: !1, line: 7, type: !3)
!26 = !DILocation(line: 7, column: 14, scope: !22)
!27 = !DILocation(line: 8, column: 8, scope: !28)
!28 = distinct !DILexicalBlock(scope: !22, file: !1, line: 8, column: 7)
!29 = !DILocation(line: 8, column: 7, scope: !28)
!30 = !DILocation(line: 8, column: 10, scope: !28)
!31 = !DILocation(line: 8, column: 7, scope: !22)
!32 = !DILocalVariable(name: "tmp", scope: !33, file: !1, line: 9, type: !3)
!33 = distinct !DILexicalBlock(scope: !28, file: !1, line: 8, column: 15)
!34 = !DILocation(line: 9, column: 10, scope: !33)
!35 = !DILocation(line: 9, column: 24, scope: !33)
!36 = !DILocation(line: 10, column: 15, scope: !33)
!37 = !DILocation(line: 10, column: 14, scope: !33)
!38 = !DILocation(line: 10, column: 17, scope: !33)
!39 = !DILocation(line: 10, column: 5, scope: !33)
!40 = !DILocation(line: 10, column: 12, scope: !33)
!41 = !DILocation(line: 11, column: 15, scope: !33)
!42 = !DILocation(line: 11, column: 14, scope: !33)
!43 = !DILocation(line: 11, column: 17, scope: !33)
!44 = !DILocation(line: 11, column: 5, scope: !33)
!45 = !DILocation(line: 11, column: 12, scope: !33)
!46 = !DILocation(line: 12, column: 14, scope: !33)
!47 = !DILocation(line: 12, column: 10, scope: !33)
!48 = !DILocation(line: 12, column: 26, scope: !33)
!49 = !DILocation(line: 12, column: 21, scope: !33)
!50 = !DILocation(line: 12, column: 19, scope: !33)
!51 = !DILocation(line: 12, column: 6, scope: !33)
!52 = !DILocation(line: 12, column: 8, scope: !33)
!53 = !DILocation(line: 13, column: 10, scope: !33)
!54 = !DILocation(line: 13, column: 5, scope: !33)
!55 = !DILocation(line: 14, column: 14, scope: !33)
!56 = !DILocation(line: 14, column: 13, scope: !33)
!57 = !DILocation(line: 14, column: 5, scope: !33)
!58 = !DILocation(line: 17, column: 11, scope: !22)
!59 = !DILocation(line: 17, column: 10, scope: !22)
!60 = !DILocation(line: 17, column: 13, scope: !22)
!61 = !DILocation(line: 17, column: 3, scope: !22)
!62 = !DILocation(line: 18, column: 1, scope: !22)
!63 = distinct !DISubprogram(name: "main", scope: !1, file: !1, line: 20, type: !64, scopeLine: 20, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !16)
!64 = !DISubroutineType(types: !65)
!65 = !{!4}
!66 = !DILocalVariable(name: "r", scope: !63, file: !1, line: 21, type: !4)
!67 = !DILocation(line: 21, column: 7, scope: !63)
!68 = !DILocalVariable(name: "p", scope: !63, file: !1, line: 22, type: !3)
!69 = !DILocation(line: 22, column: 8, scope: !63)
!70 = !DILocation(line: 22, column: 20, scope: !63)
!71 = !DILocation(line: 23, column: 8, scope: !63)
!72 = !DILocation(line: 23, column: 3, scope: !63)
!73 = !DILocation(line: 24, column: 11, scope: !63)
!74 = !DILocation(line: 24, column: 7, scope: !63)
!75 = !DILocation(line: 24, column: 5, scope: !63)
!76 = !DILocation(line: 25, column: 8, scope: !63)
!77 = !DILocation(line: 25, column: 3, scope: !63)
!78 = !DILocation(line: 26, column: 10, scope: !63)
!79 = !DILocation(line: 26, column: 3, scope: !63)
